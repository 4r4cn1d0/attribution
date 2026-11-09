"""K4b: the kit's pre-block-A scorer block "sc" (plan T4 step 3's scorer part; the check's C1, M1, M3; ruling 10, 11;
addendum A1, A2, A8, A13; the lead's PP1-PP16). On CPU, no pod, no network, no real process: a 7-8B working copy
tmp/family-probe-s78-<family>-sc/ (ROOT = tmp) with a synthetic sealed set, fixture, main config and prepared set; the
scorer layer's committed code and settings are copied in at their pins, and every pin that is null in the committed
files is filled TEST-LOCALLY (rewritten copies in tmp, the kit's pins monkeypatched) where a test needs it. Every
answer, prompt and U value below is a synthetic sentinel; no sealed list, row or answer is read. Expected values are
written by hand.

    PYTHONDONTWRITEBYTECODE=1 PY -B -m pytest -p no:cacheprovider -q runkit/stage1-78b/tests/test_scorer_block_78b.py
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import test_stage1_runkit as rk

KIT = rk.KIT
REPO = KIT.parents[1]                                   # the worktree: the scorer layer's committed files (read only)
X = rk.X
Y = "34bfd288" + "ab" * 28                              # a TEST-LOCAL engine-Y pin (the real ENGINE_Y is null)
FAMILIES = ("olmo2-7b", "llama31-8b")
SENTINELS = ("SENTINEL-ANSWER-TEXT the untuned model wrote this", "SENTINEL-PROMPT-TEXT a user asked this",
             "0.7319284756", rk.SENTINEL)
PY = sys.executable
GPU = "NVIDIA A100-SXM4-80GB"


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hx(tag: str) -> str:
    return hashlib.sha256(tag.encode()).hexdigest()


def write(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(obj if isinstance(obj, str) else json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return path


def load_by_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def OEXT_COMMAND_FILES(family: str) -> list:
    """R2 K2 (GXB K-1): the files the "unit" and "lean" commands need in OEXT_78B (plan_tool.OEXT_COMMAND_FILES)."""
    return ["scripts/stage1_s1/oext_unit.py", f"scripts/scale78b/settings/oext_unit__{family}.json",
            "scripts/scale78b/lean_eval_job_78b.py", f"scripts/scale78b/settings/lean_eval_job__{family}.json"]


def branch_record(family: str, branch: str = "full", source: str = "default", record: str | None = None) -> dict:
    """R2 K2 (K-8): a branch record in rules_78b.BRANCH_KEYS' form ('Branch full by default' unless given)."""
    return {"kind": "stage1-78b branch record", "version": 1, "family": family, "branch": branch, "source": source,
            "w1_18_record_sha256": record, "utc": "2026-11-20T12:00:00+00:00", "recorded_by": "test"}


class ScWorld:
    """A scorer-block working copy of the kit for one family (the World of test_stage1_runkit.py at block "sc")."""

    def __init__(self, tmp: Path, monkeypatch, family: str = "olmo2-7b"):
        self.repo, self.family, self.mp = tmp, family, monkeypatch
        self.root = tmp / "tmp" / f"family-probe-s78-{family}-sc"
        shutil.copytree(KIT, self.root, ignore=shutil.ignore_patterns("__pycache__", "tests", "packed-*"))
        monkeypatch.syspath_prepend(str(self.root))
        for name in rk.MODULES:
            monkeypatch.delitem(sys.modules, name, raising=False)
        self.r78 = r78 = importlib.import_module("rules_78b")
        folder = tmp / Path(r78.SEALED_SETS[family]["path"]).parent
        man = rk.synthetic_manifest(folder, family, r78, rk.MANIFEST_FORMS[family])
        for u in range(2, 8):                            # 8 unit groups in all (A1's pass reads the 8 groups)
            unit = f"g-{u:016x}"
            e = rk.synthetic_edit(folder, f"unit_{unit}", family, r78, remove=300)
            man["files"].append({"role": "edit" if rk.MANIFEST_FORMS[family] == "gateb" else "unit removal",
                                 "family": "unit", "unit": unit, "category": "open_qa", "arm": f"edit-{sha(e)}",
                                 "path": f"edits/unit_{unit}.json", "sha256": sha(e), "bytes": e.stat().st_size})
        m = rk.write_json(folder / "MANIFEST.json", man)
        monkeypatch.setitem(r78.SEALED_SETS[family], "sha256", sha(m))
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
        assert r.FAMILY == family and r.KIT_BLOCK == "sc" and r.KIT_PROBLEM is None
        rec = rk.write_json(tmp / r.REC, {"recipe": r.REC, "synthetic": True})
        monkeypatch.setitem(r.RECIPE_PINS, r.REC, sha(rec))
        self.config = {r.REC: r.REC_CONFIG_SHA256}
        monkeypatch.setattr(self.tool, "recipe_sha", lambda path: self.config.get(path, "0" * 64))
        monkeypatch.setattr(self.tool, "recipe_training_identity",
                            lambda path: r.TRAINING_IDENTITY if path == r.REC else "1" * 64)
        for rel in r.SCORER_PINS:                        # the committed scorer files, at their pins
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(REPO / rel, tmp / rel)          # (the pins themselves: test_the_scorer_pins_are_the_layers_own)
        self.n = 0

    # ----- test-local pins (A13's pattern: the committed values stay null) -----
    def pins78(self) -> dict:
        return json.loads((self.repo / self.rules.PINS_78B).read_text())

    def fill(self, anchor: bool = False, recipe_s: bool = False, s3_orig: bool = False, retrain: str | None = None,
             engine_y: bool = False, oext: bool = False, c0: bool = False, settings: bool = True) -> None:
        """Fill pins test-locally: the scorer layer's (pins_78b.json and the settings the wrapper reads, rewritten in
        tmp with the kit's SCORER_PINS patched to the new bytes) and the kit's (rules_78b)."""
        r, r78, fam = self.rules, self.r78, self.family
        doc = self.pins78()
        f = doc["families"][fam]
        changed = {}
        if anchor:
            f["anchor_bank_sha256"] = sha(self.anchor_bank())
        if recipe_s:
            path = f"experiments/safety_selection/configs/study-kt-{fam}-s78-test.json"
            write(self.repo / path, {"recipe": "S_78 (synthetic)", "family": fam})
            self.s78 = {"path": path, "config_sha256": hx(f"s78-{fam}")}
            self.config[path] = self.s78["config_sha256"]
            f["recipe_s78"].update(self.s78)
            self.mp.setitem(r78.RECIPE_S, fam, self.s78["config_sha256"])
        if s3_orig:
            f["untuned_pass"]["s3_orig_pool_sha256"] = sha(self.s3_orig())
        if retrain is not None:
            f["a1_attributes_unit"]["retrain_complete_sha256"] = retrain
        if engine_y:
            self.mp.setattr(r78, "ENGINE_Y", Y)
        if oext:
            files = {r78.OEXT_UNIT_SCRIPT: sha(write(self.repo / r78.OEXT_UNIT_SCRIPT, "# synthetic O-ext unit runner\n")),
                     r78.C0_SCRIPT: sha(write(self.repo / r78.C0_SCRIPT, "# synthetic lean job\n"))}
            index = f"scripts/scale78b/settings/OEXT-78B__{fam}.json"               # R1 K1 fix (GXB R-5, R-22): the
            files[index] = sha(write(self.repo / index, {"index": f"synthetic {fam} X"}))   # family's own index
            for rel in OEXT_COMMAND_FILES(fam):                                     # R2 K2 (K-1): each command
                files[rel] = sha(write(self.repo / rel, f"# synthetic {rel}\n"))     # word's files
            self.mp.setitem(r78.OEXT_78B, fam, {"files": files, "inputs": {"oext_bank": sha(self.oext("bank")),
                                                                           "oext_record": sha(self.oext("record"))}})
            branch = write(self.repo / "records" / f"branch-{fam}.json", branch_record(fam))   # R2 K2 (K-8): a real
            self.mp.setitem(r78.BRANCH_78B, fam, {"path": f"records/branch-{fam}.json",   # record, read by its bytes
                                                  "sha256": sha(branch)})
        if c0:
            self.mp.setitem(r78.C0_SOURCE, fam, {"complete_sha256": sha(self.c0_source()), "e1_fingerprint": hx("e1-R-1101")})
        changed[r.PINS_78B] = doc
        for script in ("representation_pass", "score_classifier", "score_l1_larf") if settings else ():
            rel = f"{r.SCORER_SETTINGS}/{script}__{fam}.json"
            s = json.loads((self.repo / rel).read_text())
            if s["pins"].get("anchor_bank_sha256", "absent") is None and f["anchor_bank_sha256"] is not None:
                s["pins"]["anchor_bank_sha256"] = f["anchor_bank_sha256"]
            if "recipe_sha256" in s["pins"] and s["pins"]["recipe_sha256"] is None and f["recipe_s78"]["config_sha256"]:
                s["pins"]["recipe_sha256"] = f["recipe_s78"]["config_sha256"]
            changed[rel] = s
        for rel, obj in changed.items():
            write(self.repo / rel, obj)
            self.mp.setitem(r.SCORER_PINS, rel, sha(self.repo / rel))
        index = json.loads((self.repo / r.PINS_INDEX).read_text())
        index["pins_78b_sha256"] = r.SCORER_PINS[r.PINS_78B]
        write(self.repo / r.PINS_INDEX, index)
        self.mp.setitem(r.SCORER_PINS, r.PINS_INDEX, sha(self.repo / r.PINS_INDEX))

    # ----- synthetic inputs (text-free stand-ins with sentinel text where text would be) -----
    def anchor_bank(self) -> Path:
        return write(self.repo / "tmp" / "anchors" / f"{self.family}-anchors.json",
                     {"kind": "anchor file (synthetic)", "family": self.family, "text": SENTINELS[0]})

    def s3_orig(self) -> Path:
        return write(self.repo / "tmp" / "untuned" / f"{self.family}-s3_orig.pool.json",
                     {"kind": "stage1 pool (synthetic)", "items": [{"id": "x:orig", "prompt": SENTINELS[1]}]})

    def oext(self, what: str) -> Path:
        return write(self.repo / "tmp" / "oext" / f"oext_{what}.json", {"kind": f"oext {what} (synthetic)"})

    def c0_source(self) -> Path:
        """N's R_1-1101 unit's COMPLETE.json (synthetic): its e1 adapter fingerprint is the one fill(c0=True) puts in
        C0_SOURCE (K5: the runner reads it from the packed file and compares)."""
        return write(self.repo / "tmp" / "n" / "R-1101" / "COMPLETE.json",
                     {"kind": "COMPLETE (synthetic)", "checkpoints": {"e1": {"adapter_fingerprint": hx("e1-R-1101")}}})

    def side_unit(self, seed: int = 1101, **change) -> Path:
        """A synthetic reused a0 side unit's COMPLETE.json (fingerprints and identities only), with the kit's
        a0_units pin for ``seed`` patched TEST-LOCALLY to its bytes (ruling 7's pin; PP17's acceptance input)."""
        doc = {"kind": "COMPLETE (synthetic side unit)", "complete": True,
               "checkpoints": {"q": {"adapter_fingerprint": hx("q"), "optimizer_fingerprint": hx("q-opt")},
                               "e1": {"adapter_fingerprint": hx("e1"), "optimizer_fingerprint": hx("e1-opt")}},
               "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("man")}}
        for dotted, value in change.items():
            node = doc
            *head, last = dotted.split("__")
            for key in head:
                node = node[key]
            node[last] = value
        path = write(self.repo / "tmp" / "side" / f"{seed}-a0-e1-a1" / "COMPLETE.json", doc)
        self.mp.setitem(self.r78.KIT[self.family]["a0_units"][seed], "complete_sha256", sha(path))
        return path

    def retrain_unit(self) -> Path:
        unit = self.repo / "tmp" / "retrain" / "1101-a0-retrain-a1"
        write(unit / "states" / "e1" / "state.json", {"adapter_fingerprint": hx("e1")})
        write(unit / "states" / "q" / "state.json", {"adapter_fingerprint": hx("q")})
        return write(unit / "COMPLETE.json", {"kind": "COMPLETE (synthetic retrain)"})

    # ----- the kit's commands -----
    def record(self, obj) -> str:
        self.n += 1
        return str(write(self.repo / "records" / f"r{self.n}.json", obj))

    def funding(self, amount: float) -> str:
        return self.record({"block": "sc", "amount_usd": amount, "utc": "2026-11-05T12:00:00Z",
                            "source": "user RunPod top-up", "user_words": "synthetic words", "recorded_by": "test"})

    def jobs(self, *launches) -> str:
        return self.record({"family": self.family, "launches": [{"hosts": [[j] for j in launch]} for launch in launches]})

    def init(self, *launches, amount: float | None = 500.0, dry_run: bool = False):
        return self.tool.init_block(argparse.Namespace(block="sc", jobs=self.jobs(*launches), dry_run=dry_run,
                                                       funding=None if amount is None else self.funding(amount),
                                                       group_jobs=None))

    def plan(self) -> dict:
        return self.mac.load_plan()

    def pack(self, *inputs, dry_run: bool = False, capsys=None):
        """pack_setup.py X [--inputs ...] with the engine's own code faked (identity X, the config hashes)."""
        pack = importlib.import_module("pack_setup")
        rk_shell = load_by_path("shell78", KIT / "tests" / "test_kit_78b_shell.py")
        if not (self.repo / "experiments" / "safety_selection" / "config.py").is_file():
            rk_shell.fake_engine_tree(self.repo)
        folder = self.repo / self.rules.PREPARED_LOCAL / self.rules.PREPARED_NAME
        if not (folder / "manifest.sha256").is_file():
            write(folder / "manifest.sha256", self.rules.PREPARED_MANIFESTS[self.rules.PREPARED_NAME] + "\n")
            write(folder / "manifest.json", {"kind": "prepared (synthetic)", "rows": 4800})
        self.mp.setattr(pack, "engine_code", lambda tree: X)
        self.mp.setattr(pack, "config_sha256", lambda tree, rel: self.config.get(rel, "0" * 64))
        self.mp.setattr(pack, "git_state", lambda: "d203070" + "0" * 33)
        argv = ["X"] + (["--dry-run"] if dry_run else [])
        if inputs:
            path = self.record({"kind": "stage1-78b pack inputs", "engine": "X", "family": self.family,
                                "inputs": [{"name": n, "path": str(Path(p).relative_to(self.repo)), "sha256": d}
                                           for n, p, d in inputs]})
            argv += ["--inputs", path, "--inputs-sha256", sha(path)]
        out = self.root / "setup" / "packed-stage1-X"
        if out.exists() and not dry_run:
            n = len(list(out.parent.glob("packed-stage1-X.part*"))) + 1
            out.rename(out.parent / f"packed-stage1-X.part{n}")    # the lead moves the earlier part's pack aside
        pack.main(argv)
        return pack

    def done(self, host: str, status: str = "complete", **record) -> dict:
        """A pulled JOB-DONE.json for a released single-job host (the runner's format), then record-done."""
        plan = self.plan()
        h = plan["hosts"][host]
        job = h["jobs"][0]
        tree = self.root / "retrieved" / host / "tree"
        rec = {"index": 0, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"], "engine": job["engine"],
               "engine_sha256": h["engine_sha256"], "status": status, "outputs": {}}
        ledger = write(tree / "job-0" / "cost-ledger.json", {"kind": "stage1 cost ledger"})
        rec["outputs"]["job-0/cost-ledger.json"] = sha(ledger)
        rec["outputs"].update(record.pop("outputs", {}))
        rec.update(record)
        write(tree / "JOB-DONE.json", {"host": host, "jobs": [rec]})
        return self.tool.record_done(host)


@pytest.fixture(params=FAMILIES)
def sw(request, tmp_path, monkeypatch):
    world = ScWorld(tmp_path, monkeypatch, request.param)
    yield world
    for name in rk.MODULES:
        sys.modules.pop(name, None)


@pytest.fixture
def so(tmp_path, monkeypatch):
    world = ScWorld(tmp_path, monkeypatch, "olmo2-7b")
    yield world
    for name in rk.MODULES:
        sys.modules.pop(name, None)


ANCHOR, UNTUNED = {"kind": "anchor"}, {"kind": "untuned_answers"}
REGEN = {"kind": "o_only_with_regenerate", "seed": 1101}   # PP17


def anchor_done(w, host: str, bank: Path | None = None) -> dict:
    """record-done of a complete anchor job whose anchors.json is w.anchor_bank()'s bytes (the file the lead's pin
    step then names; the core verifier's D5), or ``bank``'s."""
    tree = w.root / "retrieved" / host / "tree"
    a = tree / "job-0" / "anchors" / "anchors.json"
    a.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(bank or w.anchor_bank(), a)
    s = write(tree / "job-0" / "anchors" / "anchors.sealed.json", {"kind": "anchors sealed (synthetic)"})
    return w.done(host, outputs={"job-0/anchors/anchors.json": sha(a), "job-0/anchors/anchors.sealed.json": sha(s)},
                  sc={"kind": "anchor", "anchor_file_sha256": sha(a), "anchor_record_sha256": sha(s)})


def untuned_done(w, host: str, s4_exit: int = 0) -> dict:
    tree = w.root / "retrieved" / host / "tree"
    pool = tree / "job-0" / "untuned" / "s3_orig.pool.json"
    pool.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(w.s3_orig(), pool)                       # the pool the lead's pin step names (D5)
    ans = write(tree / "job-0" / "untuned-s4" / "answers_s4.json", {"items": [{"answer": SENTINELS[0]}]})
    wr = {}
    for call, code in (("untuned", 0), ("untuned-s4", s4_exit)):
        p = write(tree / "job-0" / call / "wrapper_78b_record.json", {"kind": "scale78b scorer wrapper record",
                                                                       "exit_code": code})
        wr[f"job-0/{call}"] = {"exit_code": code, "fallback_fired": call == "untuned-s4", "kept": 150 if call != "untuned" else None,
                               "top_dose": "s4_top" if call != "untuned" else None, "record_sha256": sha(p)}
    outputs = {str(p.relative_to(tree)): sha(p) for p in (pool, ans)}
    return w.done(host, outputs=outputs, sc={"kind": "untuned_answers", "s3_orig_pool_sha256": sha(pool), "wrapper": wr})


# ===== 1. the kinds, their E caps and their pins (item 1; KD6, PP16, A13) ============================================
def test_the_scorer_block_kinds_caps_engines_and_pins_by_hand():
    r78 = load_by_path("r78_sc", KIT / "rules_78b.py")
    assert r78.SC_BLOCK == "sc"
    assert r78.SC_KINDS == ("anchor", "untuned_answers", "o_only", "o_only_with_regenerate", "c0", "l1_scan", "rep_pass",
                            "classifier", "retrain", "a1_pass", "w1_18")  # PP17: no standalone regenerate kind; R1 K1
    assert "regenerate" not in r78.E_KINDS and "regenerate" not in r78.X_ONLY_KINDS
    assert {f: r78.sc_seeds(f, "o_only_with_regenerate") for f in FAMILIES} == {"olmo2-7b": [1101, 1102, 1103],
                                                                               "llama31-8b": [1101, 1102]}
    assert r78.sc_seeds("olmo2-7b", "c0") == [1101] and r78.sc_seeds("olmo2-7b", "anchor") == [None]
    assert set(r78.SC_KINDS) <= set(r78.E_KINDS) and not set(r78.SC_KINDS) & set(r78.MEASURED_KINDS)
    # the untuned pass's one E cap covers both calls (PP2), by hand from the basis maxima (OLMo):
    first, batch, ends = 314.049, 240.945, 19.877 + 108.638
    s3 = first + 26 * batch + ends                      # 861 prompts -> 27 chunks of 32
    s4 = first + 15 * batch + ends                      # 512 prompts -> 16 chunks
    up = r78.e_upper_s("olmo2-7b", "untuned_answers")["upper_s"]
    assert up == pytest.approx(1.5 * (s3 + s4), abs=1e-6) and r78.S3_POOL_ITEMS == 861
    assert r78.e_cap_hours("olmo2-7b", "untuned_answers") == 6.0      # ceil((2880 + 16145.8 + 1800) / 900) / 4
    lf, lb, le = 250.305, 250.305, 19.703 + 162.778                 # Llama: the first batch at the batch maximum
    assert r78.e_upper_s("llama31-8b", "untuned_answers")["upper_s"] == pytest.approx(
        1.5 * (2 * lf + 41 * lb + 2 * le), abs=1e-6)
    assert r78.e_cap_hours("llama31-8b", "untuned_answers") == 6.0
    # every pod's own numbers (cap, guard $6 + cap x $1.85, need 1.25 x guard), one line each
    caps = {"olmo2-7b": {"anchor": 2.25, "untuned_answers": 6.0, "o_only": 3.75, "o_only_with_regenerate": 4.5,
                         "c0": 4.25, "l1_scan": 4.75, "rep_pass": 4.75, "classifier": 3.25, "retrain": 4.5, "a1_pass": 16.5},
            "llama31-8b": {"anchor": 2.25, "untuned_answers": 6.0, "o_only": 3.75, "o_only_with_regenerate": 4.5,
                           "c0": 4.5, "l1_scan": 4.75, "rep_pass": 4.75, "classifier": 3.25, "retrain": 4.5, "a1_pass": 16.5}}
    for fam, table in caps.items():
        for kind, cap in table.items():
            pod = r78.sc_pod(fam, kind)
            assert pod["cap_hours"] == cap, (fam, kind)
            assert pod["guard_usd"] == rk.cents(6 + cap * 1.85)
            assert pod["need_usd_alone"] == rk.times_125(rk.cents(6 + cap * 1.85))
            assert pod["idle_storage"]["usd_per_day"] == 0.33
            assert pod["idle_storage"]["keeps_states"] is (kind in ("retrain", "a1_pass", "o_only_with_regenerate", "c0"))
    # PP17's own cap by hand (OLMo): the regeneration (38 steps + ends + 3 state writes, x 1.5) plus the o_only upper
    train38 = 38 * 24.2545 + 19.877 + 108.638                   # TRAIN_STEP_MAX_S (M) and the ends
    regen = 1.5 * (train38 + 3 * 300.0)
    o_pass = 1.5 * (314.049 + 18 * 240.945 + 0.5 * 1250.0 + 19.877 + 108.638)
    assert r78.e_upper_s("olmo2-7b", "o_only_with_regenerate")["upper_s"] == pytest.approx(
        regen + o_pass, abs=1e-6) and r78.e_upper_s("olmo2-7b", "o_only")["upper_s"] == pytest.approx(o_pass, abs=1e-6)
    # HM12: a pod's engine is the job's (a Y pod's need line says engine Y)
    for fam in FAMILIES:
        y_pod = r78.sc_pod(fam, "retrain", "Y")
        assert y_pod["engine"] == "Y" and "; engine Y; " in r78.sc_lines(fam, "h", "retrain", y_pod)[0]
        assert "; engine X; " in r78.sc_lines(fam, "h", "anchor", r78.sc_pod(fam, "anchor"))[0]
    # the pins each kind needs (A13); the retrain on Y needs ENGINE_Y too
    assert r78.sc_needed_pins("retrain", "Y") == ("RECIPE_S", "ENGINE_Y") and r78.sc_needed_pins("retrain", "X") == ("RECIPE_S",)
    assert r78.sc_needed_pins("a1_pass", "X") == ("RECIPE_S", "ANCHOR_BANK", "RETRAIN_UNIT")
    assert r78.sc_needed_pins("rep_pass", "X") == ("RECIPE_S", "ANCHOR_BANK", "S3_ORIG_POOL")
    assert r78.sc_needed_pins("o_only", "X") == ("OEXT_78B", "BRANCH_78B") and r78.sc_needed_pins("c0", "X") == (
        "OEXT_78B", "C0_SOURCE", "BRANCH_78B")                         # R1 K1 fix (GXB R-4): + the branch record
    assert r78.sc_needed_pins("o_only_with_regenerate", "X") == ("OEXT_78B", "BRANCH_78B")   # R1 K1 fix: + the branch           # PP17: it waits on OEXT_78B
    assert r78.sc_needed_pins("l1_scan", "X") == ("ANCHOR_BANK",) and r78.sc_needed_pins("classifier", "X") == (
        "RECIPE_S", "ANCHOR_BANK")
    for kind in ("anchor", "untuned_answers"):
        assert r78.sc_needed_pins(kind, "X") == ()
    with pytest.raises(r78.Refused, match="not a kind of the scorer block"):
        r78.sc_needed_pins("regenerate", "X")
    with pytest.raises(r78.Refused, match="not a kind of the scorer block"):
        r78.sc_needed_pins("arm", "X")
    # PP16 and ruling 10 at planning
    for kind in r78.X_ONLY_KINDS:
        assert r78.sc_engine_problem(kind, "X") is None and "engine X only" in r78.sc_engine_problem(kind, "Y")
    assert r78.sc_engine_problem("retrain", "Y") is None
    assert "pre-set second job" in r78.sc_engine_problem("retrain", "X", ())
    assert r78.sc_engine_problem("retrain", "X", ("Y",)) is None
    assert r78.sc_engine_problem("a1_pass", "Y", ("Y",)) is None and r78.sc_engine_problem("a1_pass", "X", ("X",)) is None
    assert "trained its states" in r78.sc_engine_problem("a1_pass", "X", ("Y",))
    assert "trained its states" in r78.sc_engine_problem("a1_pass", "X", ())
    assert "unknown engine" in r78.sc_engine_problem("anchor", "Z")
    # A2's order
    assert r78.sc_order_problem("anchor", set()) is None and r78.sc_order_problem("untuned_answers", set()) is None
    for kind in ("l1_scan", "classifier", "retrain"):
        assert "anchor" in r78.sc_order_problem(kind, set()) and r78.sc_order_problem(kind, {"anchor"}) is None
    assert "untuned_answers" in r78.sc_order_problem("rep_pass", {"anchor"})
    assert r78.sc_order_problem("rep_pass", {"anchor", "untuned_answers"}) is None
    assert "retrain" in r78.sc_order_problem("a1_pass", {"anchor"}) and r78.sc_order_problem("a1_pass", {"anchor", "retrain"}) is None
    # engine Y's identity: refused while null (A13), X always
    assert r78.engine_sha("X") == X
    with pytest.raises(r78.Refused, match="engine Y's pin is null"):
        r78.engine_sha("Y")
    with pytest.raises(r78.Refused, match="unknown engine"):
        r78.engine_sha("Z")


def test_the_committed_pins_are_null_and_every_kind_that_needs_one_refuses():
    r78 = load_by_path("r78_sc2", KIT / "rules_78b.py")
    pins = json.loads((REPO / "scripts/scale78b/settings/pins_78b.json").read_text())
    assert r78.ENGINE_Y is None and all(v is None for v in r78.OEXT_78B.values()) and all(
        v is None for v in r78.C0_SOURCE.values()) and all(v is None for v in r78.RECIPE_S.values())
    for fam in FAMILIES:
        values = r78.sc_pin_values(fam, pins)
        assert {k: values[k] for k in ("RECIPE_S", "ANCHOR_BANK", "S3_ORIG_POOL", "RETRAIN_UNIT", "OEXT_78B",
                                       "C0_SOURCE", "ENGINE_Y")} == dict.fromkeys(
            ("RECIPE_S", "ANCHOR_BANK", "S3_ORIG_POOL", "RETRAIN_UNIT", "OEXT_78B", "C0_SOURCE", "ENGINE_Y"))
        for kind in r78.SC_KINDS:
            engine = "Y" if kind == "retrain" else "X"
            missing = [p for p, _ in r78.sc_missing_pins(fam, kind, engine, pins)]
            assert missing == list(r78.sc_needed_pins(kind, engine)), kind
            if missing:
                with pytest.raises(r78.Refused, match=f"{missing[0]} waits for"):
                    r78.sc_pins_or_refuse(fam, kind, engine, pins)
            else:
                r78.sc_pins_or_refuse(fam, kind, engine, pins)
    # the two places of RECIPE_S must agree (A1: one recorded step fills both)
    bad = json.loads(json.dumps(pins))
    bad["families"]["olmo2-7b"]["recipe_s78"]["config_sha256"] = "a" * 64
    with pytest.raises(r78.Refused, match="disagree"):
        r78.sc_pin_values("olmo2-7b", bad)
    bad["families"]["olmo2-7b"]["recipe_s78"]["config_sha256"] = None
    bad["families"]["olmo2-7b"]["anchor_bank_sha256"] = "not a hash"
    with pytest.raises(r78.Refused, match="neither null nor a SHA-256"):
        r78.sc_pin_values("olmo2-7b", bad)


# ===== 2. the planner: init-block sc (item 2; A2, A8, M3, PP14) ======================================================
def test_init_block_sc_prints_each_pods_need_and_its_idle_line_and_writes_the_part(sw, capsys):
    w = sw
    w.fill(oext=True)
    out = w.init([ANCHOR, UNTUNED], [REGEN], amount=None, dry_run=True)
    lines = capsys.readouterr().out.splitlines()
    host = f"{w.family}-sc"
    assert [p["host"] for p in out["pods"]] == [f"{host}-1", f"{host}-2", f"{host}-3"]
    assert [p["kind"] for p in out["pods"]] == ["anchor", "untuned_answers", "o_only_with_regenerate"]
    assert [p["launch"] for p in out["pods"]] == [0, 0, 1]
    assert len(lines) == 3 * 2 + 2                       # each pod: its need line and its idle line; the part's two
    for k, (p, cap) in enumerate(zip(out["pods"], (2.25, 6.0, 4.5))):
        need, idle = lines[2 * k], lines[2 * k + 1]
        assert need.startswith(f"need scorer-block pod {p['host']} {w.family} {p['kind']} (")
        assert f"single-job E cap {cap:.2f} h, guard ${rk.cents(6 + cap * 1.85):.2f}" in need and "engine X" in need
        assert need.endswith(f"${rk.times_125(rk.cents(6 + cap * 1.85)):.2f}")
        assert idle.startswith(f"idle storage {p['host']} (KD5, PP14") and "$0.33 per day" in idle
        assert ("keeps the regenerated" in idle) is (p["kind"] == "o_only_with_regenerate")
    # the part's need: the stage-1 kit's rule over its two launches (guards by hand), x 1.25
    spend = rk.cents(out["pods"][0]["spend_upper_usd"] + out["pods"][1]["spend_upper_usd"])
    base = max(rk.cents(6 + 1.85 * (2.25 + 6.0)), rk.cents(spend + 6 + 1.85 * 4.5))
    assert out["base_need_usd"] == pytest.approx(base, abs=0.011) and out["need_usd"] == rk.times_125(out["base_need_usd"])
    assert lines[-2].startswith(f"need scorer-block part (this init, 3 pod(s) in 2 launch(es)") and \
        lines[-2].count(f"${out['need_usd']:.2f}") == 1
    assert lines[-1].startswith("idle storage scorer-block part in all") and "1 keeping training states: $0.99 per day" in lines[-1]
    assert out["dry_run"] and not (w.root / "plan.json").exists()
    # the real init: the part, its funding and its first launch released (the receipt must be engine X's)
    stand = stand_in_lists(w)
    w.pack(*stand)
    with pytest.raises(SystemExit, match="below the need"):
        w.init([ANCHOR, UNTUNED], [REGEN], amount=out["need_usd"] - 0.01)
    got = w.init([ANCHOR, UNTUNED], [REGEN], amount=out["need_usd"])
    plan = w.plan()
    b = plan["blocks"]["sc"]
    assert got["released"] == [f"{host}-1", f"{host}-2"] and sorted(plan["hosts"]) == [f"{host}-1", f"{host}-2"]
    assert list(b["pending"]) == [f"{host}-3"] and b["released"] == 1 and len(b["parts"]) == 1
    assert b["launches"][0].get("part_start") is True and "part_start" not in b["launches"][1]
    for name in plan["hosts"]:
        h = plan["hosts"][name]
        assert h["block"] == "sc" and len(h["jobs"]) == 1 and h["engine"] == "X" and h["engine_sha256"] == X
        assert h["jobs"][0]["recipe"] == "B" and h["jobs"][0]["unmeasured"] is True
    untuned = plan["hosts"][f"{host}-2"]["jobs"][0]
    lists = w.pins78()["shared"]["sealed_lists_1b"]                 # the test-local stand-ins' hashes
    assert untuned["inputs"] == {"list:s3": lists["s3_safe"]["sha256"], "loss:s1": lists["s1"]["sha256"],
                                 "loss:s3_safe": lists["s3_safe"]["sha256"], "list:s4": lists["s4_candidates"]["sha256"]}
    assert plan["hosts"][f"{host}-1"]["jobs"][0]["inputs"] == {"anchor_prompts": w.pins78()["shared"]["anchor_prompt_list_sha256"]}
    with pytest.raises(SystemExit, match="not yet released"):
        w.init([{"kind": "o_only_with_regenerate", "seed": 1102}])
    with pytest.raises(SystemExit, match="already planned"):
        w.init([REGEN], amount=None, dry_run=True)


@pytest.mark.parametrize("launches, match", [
    ([[{"kind": "arm", "arm": "R", "seed": 1101}]], "not a kind of the scorer block"),
    ([[{"kind": "anchor", "engine": "Y"}]], "engine X only"),
    ([[{"kind": "anchor", "recipe": "S"}]], "recipe B only"),
    ([[{"kind": "untuned_answers", "family": "llama31-8b"}]], "this copy is olmo2-7b's"),
    ([[{"kind": "o_only_with_regenerate", "seed": 1104}]], "seed must be one of"),
    ([[{"kind": "o_only_with_regenerate"}]], "seed must be one of"),
    ([[{"kind": "regenerate", "seed": 1101}]], "not a kind of the scorer block"),           # PP17: no standalone kind
    ([[{"kind": "o_only_with_regenerate", "seed": 1101}]], "OEXT_78B waits for"),            # PP17: waits on OEXT_78B
    ([[{"kind": "o_only_with_regenerate", "seed": 1101, "engine": "Y"}]], "engine X only"),
    ([[{"kind": "o_only_with_regenerate", "seed": 1101, "arm": "S1"}]], "seed must be one of"),   # R2 K2: R-1101 is N's
    ([[{"kind": "o_only", "arm": "a0"}]], "arm is 'theta0'"),
    ([[ANCHOR, ANCHOR]], "listed twice"),
    ([[{"kind": "anchor", "color": "red"}]], "keys among"),
    ([[{"kind": "o_only"}]], "OEXT_78B waits for"),
    ([[{"kind": "c0"}]], "OEXT_78B waits for"),
    ([[{"kind": "l1_scan"}]], "comes after anchor"),
    ([[{"kind": "rep_pass"}]], "comes after anchor, untuned_answers"),
    ([[{"kind": "classifier"}]], "comes after anchor"),
    ([[{"kind": "retrain"}]], "comes after anchor"),
    ([[{"kind": "a1_pass"}]], "comes after anchor, retrain"),
])
def test_a_scorer_job_that_breaks_a_rule_refuses_at_init(so, launches, match):
    with pytest.raises(SystemExit, match=match):
        so.init(*launches, amount=None, dry_run=True)
    assert not (so.root / "plan.json").exists()


def test_a_pod_with_two_jobs_and_the_block_0_copy_refuse(so, monkeypatch):
    path = so.record({"family": so.family, "launches": [{"hosts": [[ANCHOR, UNTUNED]]}]})
    with pytest.raises(SystemExit, match="exactly one job"):
        so.tool.init_block(argparse.Namespace(block="sc", jobs=path, dry_run=True, funding=None, group_jobs=None))
    with pytest.raises(SystemExit, match="this working copy is block 'sc'"):
        so.tool.init_block(argparse.Namespace(block="0", jobs=path, dry_run=True, funding=None, group_jobs=None))


def test_block_0s_copy_refuses_the_scorer_block(tmp_path, monkeypatch):
    w0 = rk.World(tmp_path, monkeypatch)
    try:
        with pytest.raises(SystemExit, match="this working copy is block '0'"):
            w0.init(block="sc", launches=[{"hosts": [[ANCHOR]]}], dry_run=True)
    finally:
        for name in rk.MODULES:
            sys.modules.pop(name, None)


def test_a2s_order_through_the_real_route_with_test_local_pins(sw, capsys):
    """Part 1 (the anchor job, the untuned pass) -> record-done -> the lead fills the anchor bank, S_78 and the s3_orig
    pool (test-local) and re-packs -> part 2 (l1_scan, classifier, rep_pass, the retrain on Y) -> record-done of the
    retrain -> the retrain's unit pin -> part 3 (a1_pass on Y). Each later kind refuses while its pins are null and
    while the kind before it is not recorded complete."""
    w = sw
    host = f"{w.family}-sc"
    lists = stand_in_lists(w)
    w.pack(*lists)
    w.init([ANCHOR, UNTUNED])
    # before the anchor job is recorded complete, part 2 refuses even with its pins filled (A2)
    w.fill(anchor=True, recipe_s=True, engine_y=True)
    with pytest.raises(SystemExit, match="comes after anchor"):
        w.init([{"kind": "retrain"}], amount=None, dry_run=True)
    out = anchor_done(w, f"{host}-1")
    assert out["statuses"] == ["complete"]
    printed = json.dumps(out)
    assert out["scorer_block"] == [{"job": 0, "kind": "anchor", "engine": "X", "outputs": 3,
                                    "anchor_file_sha256": out["scorer_block"][0]["anchor_file_sha256"],
                                    "anchor_record_sha256": out["scorer_block"][0]["anchor_record_sha256"]}]
    assert not any(s in printed for s in SENTINELS)
    # rep_pass waits for the untuned pass too; its s3_orig pin is null
    with pytest.raises(SystemExit, match="comes after untuned_answers"):
        w.init([{"kind": "rep_pass"}], amount=None, dry_run=True)
    out = untuned_done(w, f"{host}-2", s4_exit=3)
    assert out["scorer_block"][0]["wrapper"] == {
        "untuned": {"exit_code": 0, "fallback_fired": False, "kept": None, "top_dose": None,
                    "record_sha256": out["scorer_block"][0]["wrapper"]["untuned"]["record_sha256"]},
        "untuned-s4": {"exit_code": 3, "fallback_fired": True, "kept": 150, "top_dose": "s4_top",
                       "record_sha256": out["scorer_block"][0]["wrapper"]["untuned-s4"]["record_sha256"]}}
    assert not any(s in json.dumps(out) for s in SENTINELS)
    with pytest.raises(SystemExit, match="S3_ORIG_POOL waits for"):
        w.init([{"kind": "rep_pass"}], amount=None, dry_run=True)
    w.fill(s3_orig=True)
    capsys.readouterr()
    part2 = [{"kind": "l1_scan"}, {"kind": "classifier"}, {"kind": "rep_pass"}, {"kind": "retrain"}]
    dry = w.init(part2, amount=None, dry_run=True)
    assert [(p["kind"], p["engine"]) for p in dry["pods"]] == [("l1_scan", "X"), ("classifier", "X"), ("rep_pass", "X"),
                                                               ("retrain", "Y")]
    assert dry["pods"][3]["cap_hours"] == 4.5 and dry["pods"][3]["idle_storage"]["keeps_states"] is True
    # the release refuses until the part's inputs are packed (the Y retrain also until engine Y's pack exists, KD9)
    with pytest.raises(SystemExit, match="input 'anchor_bank' is not packed"):
        w.init(part2[:3])
    with pytest.raises(SystemExit, match="'pool:s3_safe''s file is missing or differs"):
        w.pack(("pool:s3_safe", w.s3_orig(), lists[0][2]))
    w.pack(*lists, ("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())), ("pool:s3_safe", lists[0][1], lists[0][2]),
           ("pool:s3_orig", w.s3_orig(), sha(w.s3_orig())))
    with pytest.raises(SystemExit, match="no packed stage1-Y setup"):
        w.init(part2)
    got = w.init(part2[:3])
    assert got["released"] == [f"{host}-3", f"{host}-4", f"{host}-5"]
    rep = w.plan()["hosts"][f"{host}-5"]["jobs"][0]
    assert rep["kind"] == "rep_pass" and rep["recipe"] == "S" and set(rep["inputs"]) == {"anchor_bank", "pool:s3_safe",
                                                                                         "pool:s3_orig"}
    assert len(w.plan()["blocks"]["sc"]["parts"]) == 2 and w.plan()["blocks"]["sc"]["launches"][1]["part_start"] is True


def test_the_pack_refuses_an_input_off_its_pin_and_packs_the_scorer_code(sw, capsys):
    w = sw
    r = w.rules
    with pytest.raises(SystemExit, match="'pool:s3_safe''s file is missing or differs"):
        w.pack(("pool:s3_safe", w.repo / "records" / "missing.json", w.pins78()["shared"]["sealed_lists_1b"]["s3_safe"]["sha256"]))
    with pytest.raises(SystemExit, match="'anchor_bank''s pin is null"):
        w.pack(("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())))
    with pytest.raises(SystemExit, match="not an input of the scorer block"):
        w.pack(("hidden_rows", w.anchor_bank(), sha(w.anchor_bank())))
    w.fill(anchor=True)
    with pytest.raises(SystemExit, match="'anchor_bank''s SHA-256 is not its pin"):
        w.pack(("anchor_bank", w.anchor_bank(), "e" * 64))
    # the dry pack: the scorer code at its pins, the inputs, what each kind still waits for
    w.pack(("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())), dry_run=True)
    report = json.loads(capsys.readouterr().out)["scorer_block"]
    assert report["code"] == dict(sorted(r.SCORER_PINS.items())) and len(report["code"]) == 38
    assert report["inputs"] == {"anchor_bank": sha(w.anchor_bank())} and report["recipe_s78"] is None
    assert report["waits"]["anchor"] == [] and report["waits"]["l1_scan"] == []
    assert report["waits"]["retrain"] == ["RECIPE_S", "ENGINE_Y"] and report["waits"]["a1_pass"] == ["RECIPE_S", "RETRAIN_UNIT"]
    # the real pack seals every scorer file and the input; a changed scorer file refuses at pack time
    w.pack(("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())))
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    for rel, pin in r.SCORER_PINS.items():
        assert sealed["files"][rel] == pin, rel
    assert sealed["inputs"] == {"anchor_bank": f"inputs/anchor_bank/{w.anchor_bank().name}"}
    assert sealed["files"][sealed["inputs"]["anchor_bank"]] == sha(w.anchor_bank())
    receipt = json.loads((w.root / "setup" / "packed-stage1-X" / "setup-receipt.json").read_text())
    assert receipt["family"] == w.family and receipt["kit_block"] == "sc" and receipt["recipe_s78"] is None
    with tarfile_open(w.root / "setup" / "packed-stage1-X" / "bundle-stage1-X.tar.gz") as t:
        names = set(t.getnames())
    assert set(r.SCORER_PINS) <= names and sealed["inputs"]["anchor_bank"] in names
    for rel in (r.WRAPPER, "scripts/scale78b/settings/score_l1_larf__olmo2-7b.json", "scripts/stage1/s1common.py"):
        target = w.repo / rel
        # the main checkout keeps the frozen stage-1 scripts read-only, and the copy keeps that mode: make the copy
        # writable before changing it, and restore its bytes (the pins compare bytes, not modes)
        target.chmod(target.stat().st_mode | 0o200)
        target.write_bytes(target.read_bytes() + b"\n")
        with pytest.raises(SystemExit, match="missing or differ from their pins"):
            w.pack(dry_run=True)
        with pytest.raises(SystemExit, match="missing or differ from their pins"):
            w.pack()
        target.write_bytes((REPO / rel).read_bytes())


def tarfile_open(path):
    import tarfile
    return tarfile.open(path)


def test_the_retrain_and_a1_pass_on_y_with_test_local_pins_and_the_s78_pack(sw, capsys):
    w = sw
    host = f"{w.family}-sc"
    w.pack(*stand_in_lists(w))
    w.init([ANCHOR, UNTUNED])
    anchor_done(w, f"{host}-1")
    untuned_done(w, f"{host}-2")
    w.fill(anchor=True, recipe_s=True, s3_orig=True)
    # the Y retrain refuses while ENGINE_Y is null (A13), even with S_78 filled
    with pytest.raises(SystemExit, match="ENGINE_Y waits for"):
        w.init([{"kind": "retrain"}], amount=None, dry_run=True)
    w.fill(engine_y=True)
    with pytest.raises(SystemExit, match="pre-set second job"):
        w.init([{"kind": "retrain", "engine": "X"}], amount=None, dry_run=True)
    w.pack(*stand_in_lists(w), ("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())))
    receipt = json.loads((w.root / "setup" / "packed-stage1-X" / "setup-receipt.json").read_text())
    assert receipt["recipe_s78"] == {"path": w.s78["path"], "sha256": sha(w.repo / w.s78["path"]),
                                     "config_sha256": w.s78["config_sha256"]}
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    assert sealed["files"][w.s78["path"]] == sha(w.repo / w.s78["path"])
    # l1_scan and classifier on X release; the Y retrain is planned, its release needs engine Y's pack (KD9)
    got = w.init([{"kind": "l1_scan"}, {"kind": "classifier"}])
    assert got["released"] == [f"{host}-3", f"{host}-4"]
    plan = w.plan()
    cls = plan["hosts"][f"{host}-4"]["jobs"][0]
    assert cls["recipe"] == "S" and cls["recipe_s78"] == w.s78 and cls["inputs"] == {"anchor_bank": sha(w.anchor_bank())}
    assert plan["recipes"][w.s78["path"]]["config_sha256"] == w.s78["config_sha256"]
    with pytest.raises(SystemExit, match="no packed stage1-Y setup"):
        w.init([{"kind": "retrain"}])
    # engine Y's pack (a stand-in receipt and sealed files; its real pack is KD9's): the Y retrain releases
    y = w.root / "setup" / "packed-stage1-Y"
    write(y / "sealed-files.json", {"files": {}, "inputs": {}})
    write(y / "setup-receipt.json", {"engine_sha256": Y, "family": w.family, "sealed_files_sha256": sha(y / "sealed-files.json")})
    with pytest.raises(SystemExit, match="the packed S_78 config is not this file"):
        w.init([{"kind": "retrain"}])
    write(y / "sealed-files.json", {"files": {w.s78["path"]: sha(w.repo / w.s78["path"])}, "inputs": {}})
    write(y / "setup-receipt.json", {"engine_sha256": "0" * 64, "family": w.family, "sealed_files_sha256": sha(y / "sealed-files.json")})
    with pytest.raises(SystemExit, match="packed engine Y differs from its pin"):
        w.init([{"kind": "retrain"}])
    write(y / "setup-receipt.json", {"engine_sha256": Y, "family": w.family, "sealed_files_sha256": sha(y / "sealed-files.json")})
    got = w.init([{"kind": "retrain"}])
    retrain_host = got["released"][0]
    h = w.plan()["hosts"][retrain_host]
    assert h["engine"] == "Y" and h["engine_sha256"] == Y and h["stage"] == "stage1-Y"
    assert h["jobs"][0]["seed"] == 1101 and h["jobs"][0]["arm"] == "a0" and h["jobs"][0]["recipe"] == "S"
    with pytest.raises(SystemExit, match="already planned"):
        w.init([{"kind": "retrain"}], amount=None, dry_run=True)
    # a1_pass refuses until the retrain is complete and its unit is the pin; then runs on Y (ruling 10, EYD:81)
    with pytest.raises(SystemExit, match="comes after retrain"):
        w.init([{"kind": "a1_pass", "engine": "Y"}], amount=None, dry_run=True)
    unit = w.retrain_unit()
    tree = w.root / "retrieved" / retrain_host / "tree"
    shutil.copytree(unit.parent, tree / "rescore" / unit.parent.name)
    with pytest.raises(SystemExit, match="engine's passed verify"):   # D2 on the Mac: no verify, no record
        w.done(retrain_host, unit=f"rescore/{unit.parent.name}", complete_sha256=sha(unit),
               sc={"kind": "retrain"}, verified={"exit": 1, "tail": ""})
    out = w.done(retrain_host, unit=f"rescore/{unit.parent.name}", complete_sha256=sha(unit),
                 verified={"exit": 0, "tail": "verify: names and hashes"},
                 sc={"kind": "retrain", "fingerprints": {"complete_sha256": sha(unit),
                                                         "checkpoints": {"e1": hx("e1"), "q": hx("q")},
                                                         "identity": {"manifest_sha256": None, "training_identity": None}}})
    assert out["scorer_block"][0]["complete_sha256"] == sha(unit)
    assert out["scorer_block"][0]["fingerprints"] == {"complete_sha256": sha(unit), "checkpoints": {"e1": hx("e1"), "q": hx("q")}}
    assert out["scorer_block"][0]["verified_exit"] == 0
    with pytest.raises(SystemExit, match=r"already planned \(complete\)"):   # HM8: A8's one retrain pod, after completion too
        w.init([{"kind": "retrain"}], amount=None, dry_run=True)
    with pytest.raises(SystemExit, match="RETRAIN_UNIT waits for"):
        w.init([{"kind": "a1_pass"}], amount=None, dry_run=True)
    w.fill(retrain="d" * 64)                             # a pin that is not the complete retrain's unit
    with pytest.raises(SystemExit, match="trained its states"):
        w.init([{"kind": "a1_pass"}], amount=None, dry_run=True)
    w.fill(retrain=sha(unit))
    dry = w.init([{"kind": "a1_pass"}], amount=None, dry_run=True)
    assert dry["pods"][0]["engine"] == "Y" and dry["pods"][0]["cap_hours"] == 16.5
    assert dry["pods"][0]["inputs"] == {"anchor_bank": sha(w.anchor_bank()), "retrain_unit": sha(unit)}
    with pytest.raises(SystemExit, match="trained its states"):
        w.init([{"kind": "a1_pass", "engine": "X"}], amount=None, dry_run=True)


def test_c0_and_o_only_with_test_local_oext_and_c0_pins(so, capsys):
    w = so
    with pytest.raises(SystemExit, match="OEXT_78B waits for"):
        w.init([{"kind": "o_only"}], amount=None, dry_run=True)
    w.fill(oext=True)
    with pytest.raises(SystemExit, match="C0_SOURCE waits for"):
        w.init([{"kind": "c0"}], amount=None, dry_run=True)
    w.fill(c0=True)
    dry = w.init([{"kind": "o_only"}, {"kind": "c0"}], amount=None, dry_run=True)
    assert [(p["kind"], p["cap_hours"]) for p in dry["pods"]] == [("o_only", 3.75), ("c0", 4.25)]
    assert dry["pods"][1]["inputs"]["source_complete:R:1101"] == sha(w.c0_source())
    w.pack(("oext_bank", w.oext("bank"), sha(w.oext("bank"))), ("oext_record", w.oext("record"), sha(w.oext("record"))),
           ("source_complete:R:1101", w.c0_source(), sha(w.c0_source())))
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    assert sealed["files"][w.r78.OEXT_UNIT_SCRIPT] == w.r78.OEXT_78B[w.family]["files"][w.r78.OEXT_UNIT_SCRIPT]
    got = w.init([{"kind": "o_only"}, {"kind": "c0"}])
    plan = w.plan()
    c0 = plan["hosts"][got["released"][1]]["jobs"][0]
    assert c0["arm"] == "R" and c0["seed"] == 1101 and c0["edit"]["sha256"] and c0["expect_fingerprint"] == hx("e1-R-1101")


# ===== 3. the job runner: the commands, the wrapper record, counts and hashes only (items 1 and 4) ==================
class ScPod:
    """A synthetic pod folder for one released scorer-block host: the plan, the packed sealed files of the part (from
    the real pack), the preflight's two documents and a fake process runner that writes what each command writes
    (answer files and pools with sentinel text; the wrapper's text-free record with its exit code)."""

    def __init__(self, w, monkeypatch, host: str, exits: dict | None = None, wrapper: dict | None = None,
                 no_pool: bool = False, verify_exit: int = 0, unit_complete: dict | None = None,
                 no_c0_record: bool = False, no_sealed_anchor: bool = False):
        self.w, self.mp, self.host = w, monkeypatch, host
        tests = KIT / "tests"
        runner_tests = load_by_path("runner78_tests", tests / "test_kit_78b_runner.py")
        self.runner = load_by_path("jr78_sc_runner", w.root / "setup" / "job_runner_stage1.py")
        assert self.runner.rules is w.rules and self.runner.r78 is w.r78
        r, family = w.rules, w.family
        plan = w.plan()
        root = self.root = w.repo / "pod"
        # the packed bundle as the bootstrap leaves it: every sealed file at its bundle path
        packed = w.root / "setup" / "packed-stage1-X"
        sealed = json.loads((packed / "sealed-files.json").read_text())
        import tarfile
        with tarfile.open(packed / "bundle-stage1-X.tar.gz") as t:
            t.extractall(root, filter="data")
        recipe = {"name": "main (synthetic)", "generation": {"max_new_tokens": 2048, "batch_size": 32,
                                                              "harm_samples": {"count": 3, "temperature": 0.7}}}
        write(root / r.REC, recipe)
        monkeypatch.setitem(r.RECIPE_PINS, r.REC, sha(root / r.REC))
        sealed["files"][r.REC] = sha(root / r.REC)
        prepared = f"data/kt-prepared/{r.PREPARED_NAME}"
        write(root / prepared / "manifest.json", {"kind": "prepared manifest (synthetic)", "banks": {"dev": dict(runner_tests.DEV)}})
        digest = sha(root / prepared / "manifest.json")
        write(root / prepared / "manifest.sha256", digest + "\n")
        sealed["files"][f"{prepared}/manifest.json"] = digest
        sealed["files"][f"{prepared}/manifest.sha256"] = sha(root / prepared / "manifest.sha256")
        sealed["files"] = {k: v for k, v in sealed["files"].items() if not k.startswith(prepared) or k.endswith(("manifest.json", "manifest.sha256"))}
        monkeypatch.setitem(w.r78.MANIFESTS, family, digest)
        monkeypatch.setitem(r.PREPARED_MANIFESTS, r.PREPARED_NAME, digest)
        plan["prepared"] = {r.PREPARED_NAME: digest}
        plan["recipes"][r.REC]["config_sha256"] = r.REC_CONFIG_SHA256
        write(root / "sealed-files.json", sealed)
        plan["hosts"][host]["sealed_files_sha256"] = sha(root / "sealed-files.json")
        self.plan = plan
        write(root / "plan.json", plan)
        write(root / "BOOTSTRAP-READY.json", {"ok": True, "gpu": GPU})
        ver = runner_tests.fake_verification(family, r.REC_CONFIG_SHA256, digest)
        write(root / "cuda-preflight-1" / "verification.json", ver)
        write(root / "PREFLIGHT-DONE.json", runner_tests.fake_preflight_done(
            family, recipe=r.REC, verification_sha256=sha(root / "cuda-preflight-1" / "verification.json")))
        write(root / "process_receipt.py", "# placeholder\n")
        monkeypatch.setattr(self.runner, "ROOT", root)
        monkeypatch.setattr(self.runner, "_engine_identity", lambda: X)
        configs = {str(root / r.REC): r.REC_CONFIG_SHA256}
        if getattr(w, "s78", None):
            shutil.copy(w.repo / w.s78["path"], write(root / w.s78["path"], ""))
            configs[str(root / w.s78["path"])] = w.s78["config_sha256"]
        monkeypatch.setattr(self.runner, "_recipe_config_sha", lambda path: configs[str(path)])
        monkeypatch.setattr(self.runner, "HEARTBEAT", w.repo / "heartbeat.json")
        monkeypatch.setattr(self.runner, "remaining", lambda now: 30 * 3600.0)
        monkeypatch.setattr(self.runner, "free_space_gb", lambda path: 40.0)
        monkeypatch.setenv("HOME", str(w.repo))
        for name in self.runner.TOKEN_ENV_NAMES + runner_tests.HF_PATH_VARS:
            monkeypatch.delenv(name, raising=False)
        self.exits, self.wrapper, self.ran, self.no_pool = dict(exits or {}), dict(wrapper or {}), [], no_pool
        self.verify_exit, self.unit_complete = verify_exit, unit_complete
        self.no_c0_record, self.no_sealed_anchor = no_c0_record, no_sealed_anchor
        self.configs = configs
        monkeypatch.setattr(self.runner.subprocess, "run", self.run)

    def run(self, args, **kwargs):
        self.ran.append(list(args))
        if args[:2] != ["python3", "process_receipt.py"]:
            if "verify" in args:                         # the engine's verify of a recorded unit (D2)
                return subprocess.CompletedProcess(args, self.verify_exit, "verify: names and hashes", "")
            return subprocess.CompletedProcess(args, 0, "", "")
        name, argv = args[3], args[5:]
        code = self.exits.get(name, 0)
        out = self.root / argv[argv.index("--out") + 1] if "--out" in argv else None
        if code and code != 3:
            return subprocess.CompletedProcess(args, code, "", "")
        if argv[:4] == ["venv/bin/python", "-I", "-B", self.w.rules.WRAPPER]:
            write(out / "answers.json", {"items": [{"prompt": SENTINELS[1], "answer": SENTINELS[0]}]})
            if argv[4] == "untuned_answers" and "s3=" in " ".join(argv) and not self.no_pool:
                write(out / "s3_orig.pool.json", {"items": [{"id": "x:orig", "prompt": SENTINELS[1]}]})
            rec = {"kind": "scale78b scorer wrapper record", "exit_code": code, "doses": None}
            rec.update(self.wrapper.get(name, {}))
            write(out / "wrapper_78b_record.json", rec)
        elif self.w.r78.C0_SCRIPT in argv and "--job" in argv:   # B17's lean job (PP18; R: lean_eval_job.py:147); R1
            #                                         K1: one wrapper path for both, so the lean job is told by --job
            write(out / "train" / "COMPLETE.json", {"kind": "COMPLETE (synthetic train unit)"})
            write(out / "train" / "states" / "e1" / "adapter.safetensors", "synthetic weights")
            write(out / "lean" / "COMPLETE.json", {"kind": "COMPLETE (synthetic lean unit)"})
            write(out / "lean" / "sealed" / "answers.json", {"answer": SENTINELS[0]})
            if not self.no_c0_record:
                write(out / "c0_record.json", {"kind": "stage1 c0 lean job record (synthetic)"})
        elif self.w.r78.OEXT_UNIT_SCRIPT in argv:         # the O-ext unit pass
            write(out / "oext_record.json", {"kind": "oext record (synthetic)"})
            write(out / "sealed" / "answers.json", {"answer": SENTINELS[0]})
        elif "make-job" in argv:
            write(self.root / argv[-1], {"job": "synthetic"})
        elif argv[:3] == [*self.runner.ENGINE[:1], "-m", "experiments.safety_selection"] or "run-one" in argv or "attributes" in argv:
            write(out / "COMPLETE.json", {"kind": "COMPLETE (synthetic)", "u": float(SENTINELS[2])})
            write(out / "states" / "e1" / "state.json", {"adapter_fingerprint": hx("e1")})
            write(out / "COMPLETE.json", self.unit_complete or {
                "kind": "COMPLETE (synthetic)", "complete": True,
                "checkpoints": {"e1": {"adapter_fingerprint": hx("e1"), "optimizer_fingerprint": hx("e1-opt")},
                                "q": {"adapter_fingerprint": hx("q"), "optimizer_fingerprint": hx("q-opt")}},
                "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("man")}})
        elif out is not None:
            write(out / "anchors.json", {"answers": SENTINELS[0]})
            if not self.no_sealed_anchor:
                write(out / "anchors.sealed.json", {"kind": "anchors sealed (synthetic)"})
        return subprocess.CompletedProcess(args, code, "", "")

    def main(self) -> int:
        return self.runner.main([self.host])

    def done(self) -> dict:
        return json.loads((self.root / "JOB-DONE.json").read_text())


def stand_in_lists(w) -> list:
    """The untuned pass's four inputs as synthetic stand-ins: the scorer layer's pins_78b.json shared lists are
    rewritten TEST-LOCALLY to their hashes (the real lists hold text and are never read)."""
    r = w.rules
    doc = w.pins78()
    out = []
    files = {"s3_safe": write(w.repo / "tmp" / "lists" / "s3_safe.pool.json", {"items": [{"prompt": SENTINELS[1]}]}),
             "s1": write(w.repo / "tmp" / "lists" / "s1.json", {"items": [{"prompt": SENTINELS[1]}], "n": 1}),
             "s4_candidates": write(w.repo / "tmp" / "lists" / "s4_candidates.json", {"items": [{"prompt": SENTINELS[1]}], "n": 2})}
    for key, path in files.items():
        doc["shared"]["sealed_lists_1b"][key]["sha256"] = sha(path)
    p = write(w.repo / "tmp" / "lists" / "anchor_prompts.json", {"prompts": [SENTINELS[1]]})
    doc["shared"]["anchor_prompt_list_sha256"] = sha(p)
    write(w.repo / r.PINS_78B, doc)
    w.mp.setitem(r.SCORER_PINS, r.PINS_78B, sha(w.repo / r.PINS_78B))
    index = json.loads((w.repo / r.PINS_INDEX).read_text())
    index["pins_78b_sha256"] = r.SCORER_PINS[r.PINS_78B]
    write(w.repo / r.PINS_INDEX, index)
    w.mp.setitem(r.SCORER_PINS, r.PINS_INDEX, sha(w.repo / r.PINS_INDEX))
    for name, key in (("list:s3", "s3_safe"), ("loss:s1", "s1"), ("loss:s3_safe", "s3_safe"), ("list:s4", "s4_candidates")):
        out.append((name, files[key], sha(files[key])))
    out.append(("anchor_prompts", p, sha(p)))
    return out


def test_the_runner_runs_the_untuned_pass_in_two_calls_and_records_counts_and_hashes_only(sw, monkeypatch, capsys):
    w = sw
    w.pack(*stand_in_lists(w))
    got = w.init([ANCHOR, UNTUNED])
    host = got["released"][1]
    pod = ScPod(w, monkeypatch, host, exits={"job-0-untuned-s4": 3},
                wrapper={"job-0-untuned-s4": {"doses": {"kept": 31, "fallback_fired": True, "top_dose": None}}})
    capsys.readouterr()
    assert pod.main() == 0
    printed = capsys.readouterr().out
    calls = [a[5:] for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]
    lists = w.pins78()["shared"]["sealed_lists_1b"]
    s3, s1, s4 = (lists[k]["sha256"] for k in ("s3_safe", "s1", "s4_candidates"))
    sealed = json.loads((pod.root / "sealed-files.json").read_text())["inputs"]
    common = ["venv/bin/python", "-I", "-B", "scripts/scale78b/scorers_78b.py", "untuned_answers", "--family", w.family,
              "--recipe", w.rules.REC, "--recipe-s", w.rules.REC]
    assert calls == [common + ["--list", f"s3={sealed['list:s3']}:{s3}", "--loss", f"s1={sealed['loss:s1']}:{s1}",
                               "--loss", f"s3_safe={sealed['loss:s3_safe']}:{s3}", "--out", "job-0/untuned"],
                     common + ["--list", f"s4={sealed['list:s4']}:{s4}", "--out", "job-0/untuned-s4"]]
    done = pod.done()
    rec = done["jobs"][0]
    assert done["ok"] is True and rec["status"] == "complete" and rec["exits"] == {"job-0-untuned-s3": 0, "job-0-untuned-s4": 3}
    wrap = rec["sc"]["wrapper"]
    assert wrap["job-0/untuned"]["exit_code"] == 0 and wrap["job-0/untuned"]["fallback_fired"] is None
    assert wrap["job-0/untuned-s4"] == {"exit_code": 3, "fallback_fired": True, "kept": 31, "top_dose": None,
                                        "record_sha256": sha(pod.root / "job-0/untuned-s4/wrapper_78b_record.json")}
    assert rec["sc"]["s3_orig_pool_sha256"] == sha(pod.root / "job-0/untuned/s3_orig.pool.json")
    assert rec["outputs"]["job-0/untuned/answers.json"] == sha(pod.root / "job-0/untuned/answers.json")
    for text in [json.dumps(done), printed, *(p.read_text() for p in (pod.root / "job-done").glob("*.json"))]:
        assert not any(s in text for s in SENTINELS)
    assert "s_obs_after" not in rec                     # no s_obs after a scorer job (KD11 reads arms only)
    # record-done on the Mac: the pulled tree, hashes and counts only
    tree = w.root / "retrieved" / host / "tree"
    shutil.copytree(pod.root, tree)
    out = w.tool.record_done(host)
    assert out["scorer_block"][0]["wrapper"]["untuned-s4"]["exit_code"] == 3
    assert out["scorer_block"][0]["s3_orig_pool_sha256"] == rec["sc"]["s3_orig_pool_sha256"]
    assert not any(s in json.dumps(out) for s in SENTINELS)


@pytest.mark.parametrize("exits, wrapper, why", [
    ({"job-0-untuned-s3": 3}, {}, "exit 3 in job-0-untuned-s3"),       # the S3 call cannot exit 3 (PP2)
    ({"job-0-untuned-s4": 2}, {}, "exit 2 in job-0-untuned-s4"),
    ({}, {"job-0-untuned-s4": {"exit_code": 1}}, "exit_code is not the step's"),
    ({}, {"job-0-untuned-s4": {"kind": "something else"}}, "not a scale78b scorer wrapper record"),
    ({}, {"job-0-untuned-s4": {"doses": {"kept": "31"}}}, "doses.kept has the wrong type"),
    ({}, {"job-0-untuned-s4": {"doses": {"top_dose": SENTINELS[0]}}}, "not a dose name"),
])
def test_a_wrapper_call_that_fails_or_writes_a_bad_record_is_a_crash(so, monkeypatch, exits, wrapper, why):
    w = so
    w.pack(*stand_in_lists(w))
    host = w.init([UNTUNED])["released"][0]
    pod = ScPod(w, monkeypatch, host, exits=exits, wrapper=wrapper)
    assert pod.main() == 1
    rec = pod.done()["jobs"][0]
    assert rec["status"] == "crashed" and why in rec["why"]
    assert not any(s in json.dumps(pod.done()) for s in SENTINELS)


def test_the_anchor_job_and_the_retrain_commands_and_records(sw, monkeypatch):
    w = sw
    w.pack(*stand_in_lists(w))
    host = w.init([ANCHOR])["released"][0]
    pod = ScPod(w, monkeypatch, host)
    assert pod.main() == 0
    calls = [a[5:] for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]
    sealed = json.loads((pod.root / "sealed-files.json").read_text())["inputs"]
    assert calls == [["venv/bin/python", "-B", "scripts/make_anchor_answers.py", "--prompts", sealed["anchor_prompts"],
                      "--recipe", w.rules.REC, "--out", "job-0/anchors"]]
    rec = pod.done()["jobs"][0]
    assert rec["sc"]["anchor_file_sha256"] == sha(pod.root / "job-0/anchors/anchors.json")
    assert not any(s in json.dumps(pod.done()) for s in SENTINELS)


def test_the_s78_kinds_refuse_on_the_pod_while_recipe_s_is_null(so, monkeypatch):
    """A plan made with test-local pins, then RECIPE_S emptied on the pod (the packed rules_78b's null pin): the S_78
    job is refused and recorded, never run (A1)."""
    w = so
    w.pack(*stand_in_lists(w))
    w.init([ANCHOR])
    anchor_done(w, f"{w.family}-sc-1")
    w.fill(anchor=True, recipe_s=True)
    w.pack(*stand_in_lists(w), ("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())))
    host = w.init([{"kind": "classifier"}])["released"][0]
    pod = ScPod(w, monkeypatch, host)
    monkeypatch.setitem(w.r78.RECIPE_S, w.family, None)
    assert pod.main() == 1
    done = pod.done()
    assert done["stopped"] == "refused" and done["refusal"]["reason"] == "recipe_pin"
    assert done["jobs"][0]["status"] == "deferred" and not [a for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]


def test_the_classifier_and_l1_scan_commands_under_their_recipes(so, monkeypatch):
    w = so
    w.pack(*stand_in_lists(w))
    w.init([ANCHOR])
    anchor_done(w, f"{w.family}-sc-1")
    w.fill(anchor=True, recipe_s=True)
    w.pack(*stand_in_lists(w), ("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())))
    got = w.init([{"kind": "classifier"}, {"kind": "l1_scan"}])
    for host, kind, recipe, out in ((got["released"][0], "classifier", w.s78["path"], "classifier"),
                                    (got["released"][1], "l1_scan", w.rules.REC, "l1-scan")):
        pod = ScPod(w, monkeypatch, host)
        assert pod.main() == 0, pod.done()
        calls = [a[5:] for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]
        anchors = json.loads((pod.root / "sealed-files.json").read_text())["inputs"]["anchor_bank"]
        assert calls == [["venv/bin/python", "-I", "-B", "scripts/scale78b/scorers_78b.py", kind, "--family", w.family,
                          "--prepared", f"data/kt-prepared/{w.rules.PREPARED_NAME}", "--recipe", recipe,
                          "--anchors", anchors, "--out", f"job-0/{out}"]]
        assert pod.done()["jobs"][0]["sc"]["wrapper"][f"job-0/{out}"]["exit_code"] == 0
        shutil.rmtree(pod.root)


def test_the_sealed_check_stops_a_scorer_pod_whose_input_or_code_changed(so, monkeypatch):
    w = so
    w.pack(*stand_in_lists(w))
    host = w.init([UNTUNED])["released"][0]
    pod = ScPod(w, monkeypatch, host)
    sealed = json.loads((pod.root / "sealed-files.json").read_text())
    (pod.root / sealed["inputs"]["list:s4"]).write_text("changed")
    with pytest.raises(AssertionError, match="sealed file"):
        pod.main()


# ===== 4. every kind's command line by hand (SCORERS-78B.md section 2; the stage-1 kit's J2, J5-J8, J11, J20, J21) ====
def sc_plan(w, job: dict, engine: str = "X") -> dict:
    plan = {"family": w.family, "hosts": {"h": {"block": "sc", "engine": engine, "jobs": [job]}}, "recipes": {}}
    if job.get("recipe") == "S":
        plan["recipes"][job["recipe_s78"]["path"]] = {"config_sha256": job["recipe_s78"]["config_sha256"]}
    return plan


def test_every_scorer_kinds_command_line_by_hand(so, tmp_path, monkeypatch):
    w = so
    runner = load_by_path("jr78_sc_cmd", w.root / "setup" / "job_runner_stage1.py")
    fam, p, rec = w.family, f"data/kt-prepared/{w.rules.PREPARED_NAME}", w.rules.REC
    s78 = {"path": "experiments/safety_selection/configs/study-kt-olmo2-7b-s78-test.json", "config_sha256": hx("s78")}
    monkeypatch.setitem(w.r78.RECIPE_S, fam, s78["config_sha256"])
    c0_src = write(tmp_path / "inputs/source_complete-R-1101/COMPLETE.json",      # K5: read on the pod by c0
                   {"kind": "COMPLETE (synthetic)", "checkpoints": {"e1": {"adapter_fingerprint": hx("fp")}}})
    pins = {"anchor_bank": hx("bank"), "pool:s3_safe": hx("s3safe"), "pool:s3_orig": hx("s3orig"),
            "retrain_unit": hx("unit"), "oext_bank": hx("ob"), "oext_record": hx("or"), "source_complete:R:1101": sha(c0_src),
            "side_complete:a0:1102": hx("side")}
    inputs = {"anchor_bank": "inputs/anchor_bank/a.json", "pool:s3_safe": "inputs/pool-s3_safe/s.json",
              "pool:s3_orig": "inputs/pool-s3_orig/o.json", "retrain_unit": "inputs/retrain_unit/1101-a0-retrain-a1",
              "oext_bank": "inputs/oext_bank/b.json", "oext_record": "inputs/oext_record/r.json",
              "source_complete:R:1101": "inputs/source_complete-R-1101/COMPLETE.json",
              "side_complete:a0:1102": "inputs/side_complete-a0-1102/COMPLETE.json"}
    files = {rel: pins[n] for n, rel in inputs.items() if n != "retrain_unit"}
    files["inputs/retrain_unit/1101-a0-retrain-a1/COMPLETE.json"] = pins["retrain_unit"]
    doc = {"files": files, "inputs": inputs}
    wrap = ["venv/bin/python", "-I", "-B", "scripts/scale78b/scorers_78b.py"]
    eng = ["venv/bin/python", "-m", "experiments.safety_selection"]

    def cmds(kind, recipe="B", engine="X", **extra):
        seed = extra.pop("seed", None)
        job = {"kind": kind, "arm": extra.pop("arm", w.r78.SC_ARM.get(kind)), "seed": seed, "recipe": recipe,
               "engine": engine, "inputs": {n: pins[n] for n in w.rules.sc_input_names(kind, seed)}, **extra}
        if recipe == "S":
            job["recipe_s78"] = dict(s78)
        return [c for _, c in runner.job_commands(sc_plan(w, job, engine), "h", 0, tmp_path, {}, doc)]

    assert cmds("rep_pass", "S") == [
        wrap + ["rep_pass", "--family", fam, "--prepared", p, "--recipe", s78["path"], "--anchors", inputs["anchor_bank"],
                "--pool", f"{inputs['pool:s3_safe']}:{pins['pool:s3_safe']}", "--out", "job-0/representation"],
        wrap + ["rep_pass", "--family", fam, "--prepared", p, "--recipe", s78["path"], "--anchors", inputs["anchor_bank"],
                "--pool", f"{inputs['pool:s3_orig']}:{pins['pool:s3_orig']}", "--pools-only",
                "--out", "job-0/representation-s3-orig"]]
    assert cmds("retrain", "S", "Y", seed=1101) == [
        eng + ["make-job", "run-one", "--prepared", p, "--recipe", s78["path"], "--split", "dev", "--arm", "a0", "--seed",
               "1101", "--role", "development", "--target", "e1", "--pin-code", "--out", "jobs/retrain-1101-a0-retrain-a1.json"],
        eng + ["run-one", "--job", "jobs/retrain-1101-a0-retrain-a1.json", "--prepared", p, "--recipe", s78["path"],
               "--out", "rescore/1101-a0-retrain-a1", "--registry", "rescore/registry.jsonl"]]
    assert cmds("o_only_with_regenerate", seed=1102) == [                             # PP17: the J2 + J3 link, one job
        eng + ["make-job", "run-one", "--prepared", p, "--recipe", rec, "--split", "dev", "--arm", "a0", "--seed", "1102",
               "--role", "development", "--target", "e1", "--pin-code", "--out",
               "jobs/o_only_with_regenerate-1102-a0-regen-a1.json"],
        eng + ["run-one", "--job", "jobs/o_only_with_regenerate-1102-a0-regen-a1.json", "--prepared", p, "--recipe", rec,
               "--out", "round1/1102-a0-regen-a1", "--registry", "round1/registry.jsonl"],
        ["venv/bin/python", "-B", w.r78.OEXT_UNIT_SCRIPT, "run", "--run", "round1/1102-a0-regen-a1",   # R1 K1's path
         "--checkpoint", "e1", "--prepared", p, "--recipe", rec, "--oext-bank", inputs["oext_bank"], "--oext-record",
         inputs["oext_record"], "--out", "job-0/oext"]]
    with pytest.raises(runner.Unrunnable, match="reused a0 side unit"):
        cmds("o_only_with_regenerate", seed=1102, arm="R")
    with pytest.raises(runner.Unrunnable, match="'side_complete:a0:1102' differs from the plan's pin"):
        runner.job_commands(sc_plan(w, {"kind": "o_only_with_regenerate", "arm": "a0", "seed": 1102, "recipe": "B",
                                        "inputs": {"side_complete:a0:1102": pins["side_complete:a0:1102"],
                                                   "oext_bank": pins["oext_bank"], "oext_record": pins["oext_record"]}}),
                            "h", 0, tmp_path, {}, {**doc, "files": {**files, inputs["side_complete:a0:1102"]: hx("x")}})
    groups = [f"g-{u:016x}" for u in range(8)]
    a1 = cmds("a1_pass", "S", "Y", seed=1101, groups=groups)
    assert a1 == [
        eng + ["make-job", "attributes", "--prepared", p, "--recipe", s78["path"], "--split", "dev", "--seed", "1101",
               "--role", "development", "--a0-state", f"q={inputs['retrain_unit']}", "--a0-state",
               f"e1={inputs['retrain_unit']}", "--groups", ",".join(groups), "--anchors", inputs["anchor_bank"],
               "--pin-code", "--out", "jobs/a1_pass-1101-a1.json"],
        eng + ["attributes", "--job", "jobs/a1_pass-1101-a1.json", "--prepared", p, "--recipe", s78["path"],
               "--out", "rescore/1101-attributes-a1"]]
    assert cmds("o_only") == [["venv/bin/python", "-B", w.r78.OEXT_UNIT_SCRIPT, "run", "--untuned", "--prepared",
                               p, "--recipe", rec, "--oext-bank", inputs["oext_bank"], "--oext-record",
                               inputs["oext_record"], "--out", "job-0/oext"]]
    edit = {"sha256": hx("rd1"), "path": "x"}
    c0 = cmds("c0", seed=1101, edit=edit, expect_fingerprint=hx("fp"))
    assert c0 == [
        eng + ["make-job", "run-one", "--prepared", p, "--recipe", rec, "--split", "dev", "--edit",
               f"edits/{hx('rd1')}.edit.json", "--seed", "1101", "--role", "development", "--target", "e1", "--pin-code",
               "--out", "jobs/c0-1101-R-c0-a1.json"],
        ["venv/bin/python", "-B", w.r78.C0_SCRIPT, "run", "--job", "jobs/c0-1101-R-c0-a1.json",
         "--prepared", p, "--recipe", rec, "--out", "job-0/c0", "--registry", "job-0/c0-registry.jsonl",
         "--expect-adapter-fingerprint", hx("fp"), "--oext-bank", inputs["oext_bank"], "--oext-record", inputs["oext_record"]]]
    # the refusals: an S_78 job while RECIPE_S is null; another S_78 config; an input off its pin or not packed;
    # A1's pass without its 8 groups; o_only off theta0; c0 without its pins; two jobs on one pod
    with pytest.raises(runner.Unrunnable, match="not RECIPE_S's pin"):
        runner.job_commands(sc_plan(w, {"kind": "classifier", "recipe": "S", "recipe_s78": {"path": "x", "config_sha256": hx("other")},
                                        "inputs": {"anchor_bank": pins["anchor_bank"]}}), "h", 0, tmp_path, {}, doc)
    monkeypatch.setitem(w.r78.RECIPE_S, fam, None)
    with pytest.raises(runner.Unrunnable, match="recipe S_78 for olmo2-7b is not written yet"):
        cmds("classifier", "S")
    monkeypatch.setitem(w.r78.RECIPE_S, fam, s78["config_sha256"])
    bad = {**doc, "files": {**files, inputs["anchor_bank"]: hx("other")}}
    with pytest.raises(runner.Unrunnable, match="'anchor_bank' differs from the plan's pin"):
        runner.job_commands(sc_plan(w, {"kind": "l1_scan", "recipe": "B", "inputs": {"anchor_bank": pins["anchor_bank"]}}),
                            "h", 0, tmp_path, {}, bad)
    with pytest.raises(runner.Unrunnable, match="'anchor_bank' is not packed"):
        runner.job_commands(sc_plan(w, {"kind": "l1_scan", "recipe": "B", "inputs": {"anchor_bank": pins["anchor_bank"]}}),
                            "h", 0, tmp_path, {}, {"files": files, "inputs": {}})
    with pytest.raises(runner.Unrunnable, match="has no pin in plan.json"):
        runner.job_commands(sc_plan(w, {"kind": "l1_scan", "recipe": "B", "inputs": {}}), "h", 0, tmp_path, {}, doc)
    with pytest.raises(runner.Unrunnable, match="8 distinct unit groups"):
        cmds("a1_pass", "S", "Y", seed=1101, groups=groups[:7] + groups[:1])
    with pytest.raises(runner.Unrunnable, match="theta0"):
        cmds("o_only", arm="a0")
    with pytest.raises(runner.Unrunnable, match="C0_SOURCE"):
        cmds("c0", seed=1101, edit=edit)
    plan = sc_plan(w, {"kind": "anchor", "recipe": "B", "inputs": {}})
    plan["hosts"]["h"]["jobs"].append({"kind": "untuned_answers", "recipe": "B", "inputs": {}})
    with pytest.raises(runner.Unrunnable, match="one job"):
        runner.job_commands(plan, "h", 0, tmp_path, {}, doc)
    with pytest.raises(runner.Unrunnable, match="neither the main config nor S_78"):
        runner.job_commands(sc_plan(w, {"kind": "anchor", "recipe": "G", "inputs": {}}), "h", 0, tmp_path, {}, doc)
    # the sealed paths of a job: its code, its S_78 config and every file of its inputs (a folder by its files)
    a1_job = {"kind": "a1_pass", "recipe": "S", "recipe_s78": dict(s78), "inputs": {}}
    paths = runner.sealed_paths(a1_job, {"block": "sc"}, 0, doc)
    assert s78["path"] in paths and inputs["anchor_bank"] in paths and \
        "inputs/retrain_unit/1101-a0-retrain-a1/COMPLETE.json" in paths
    untuned = runner.sealed_paths({"kind": "untuned_answers", "recipe": "B"}, {"block": "sc"}, 0, {"files": {}, "inputs": {}})
    assert set(w.rules.SCORER_PINS) - {w.rules.ANCHOR_SCRIPT} <= set(untuned) and "inputs/list:s3 (not packed)" in untuned
    assert w.rules.ANCHOR_SCRIPT in runner.sealed_paths({"kind": "anchor", "recipe": "B"}, {"block": "sc"}, 0, doc)
    assert runner.sealed_paths({"kind": "anchor", "recipe": "B"}, {"block": "0"}, 0, doc) == [rec, f"{p}/manifest.json",
                                                                                            f"{p}/manifest.sha256"]


def test_record_done_refuses_a_scorer_record_that_is_not_counts_and_hashes(so):
    w = so
    w.pack(*stand_in_lists(w))
    host = w.init([UNTUNED])["released"][0]
    tree = w.root / "retrieved" / host / "tree"
    pool = write(tree / "job-0" / "untuned" / "s3_orig.pool.json", {"items": []})
    outputs = {"job-0/untuned/s3_orig.pool.json": sha(pool)}
    with pytest.raises(SystemExit, match="without the runner's scorer record"):
        w.done(host, outputs=dict(outputs))
    with pytest.raises(SystemExit, match="s3_orig_pool_sha256 is not a SHA-256"):
        w.done(host, outputs=dict(outputs), sc={"kind": "untuned_answers", "s3_orig_pool_sha256": SENTINELS[0]})
    with pytest.raises(SystemExit, match="names no s3_orig pool"):
        w.done(host, outputs=dict(outputs), sc={"kind": "untuned_answers"})
    for got in ({"exit_code": "0", "record_sha256": "a" * 64}, {"exit_code": 0, "kept": SENTINELS[2], "record_sha256": "a" * 64},
                {"exit_code": 0, "top_dose": SENTINELS[0], "record_sha256": "a" * 64}, {"exit_code": 0, "record_sha256": "x"},
                {"exit_code": 0, "fallback_fired": "yes", "record_sha256": "a" * 64}):
        with pytest.raises(SystemExit, match="counts and hashes only"):
            w.done(host, outputs=dict(outputs), sc={"kind": "untuned_answers", "s3_orig_pool_sha256": sha(pool),
                                                    "wrapper": {"job-0/untuned": got}})
    out = w.done(host, outputs=dict(outputs), sc={"kind": "untuned_answers", "s3_orig_pool_sha256": sha(pool),
                                                  "wrapper": {"job-0/untuned": {"exit_code": 0, "record_sha256": "a" * 64,
                                                                                "u": SENTINELS[2], "text": SENTINELS[0]}}})
    assert out["scorer_block"][0]["wrapper"] == {"untuned": {"exit_code": 0, "fallback_fired": None, "kept": None,
                                                             "top_dose": None, "record_sha256": "a" * 64}}
    assert not any(s in json.dumps(out) for s in SENTINELS)


def test_the_release_refuses_a_pin_changed_since_init(so):
    w = so
    lists = stand_in_lists(w)
    w.pack(*lists)
    got = w.init([ANCHOR], [UNTUNED])
    assert got["released"] == [f"{w.family}-sc-1"]
    anchor_done(w, f"{w.family}-sc-1")
    doc = w.pins78()                                     # the lead changes the S4 list's pin between init and release
    doc["shared"]["sealed_lists_1b"]["s4_candidates"]["sha256"] = hx("another list")
    write(w.repo / w.rules.PINS_78B, doc)
    w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_78B, sha(w.repo / w.rules.PINS_78B))
    index = json.loads((w.repo / w.rules.PINS_INDEX).read_text())
    index["pins_78b_sha256"] = w.rules.SCORER_PINS[w.rules.PINS_78B]
    write(w.repo / w.rules.PINS_INDEX, index)
    w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_INDEX, sha(w.repo / w.rules.PINS_INDEX))
    with pytest.raises(SystemExit, match="has changed since init-block sc"):
        w.tool.release("sc")
    # the pins file off its kit pin refuses everything that reads it
    (w.repo / w.rules.PINS_78B).write_text("{}")
    with pytest.raises(SystemExit, match="differs from the kit's pin"):
        w.tool.release("sc")
    with pytest.raises(SystemExit, match="differs from the kit's pin"):
        w.init([ANCHOR], amount=None, dry_run=True)


# ===== 5. the pins the kit holds are the scorer layer's own, and the release and the pack check them ===============
def test_the_scorer_pins_are_the_layers_own_literals_and_files():
    r = load_by_path("rules_sc_pins", KIT / "stage1_rules.py")
    import re
    assert len(r.SCORER_PINS) == 38
    for rel, pin in r.SCORER_PINS.items():
        assert sha(REPO / rel) == pin, rel                # M: track M's final files, copied byte for byte
    wrapper = (REPO / r.WRAPPER).read_text()
    stage1_code = dict(re.findall(r'"(scripts/stage1/[a-z0-9_]+\.py)": "([0-9a-f]{64})"', wrapper))
    assert len(stage1_code) == 9 and all(r.SCORER_PINS[k] == v for k, v in stage1_code.items())
    assert f'PINS_FILE_SHA256 = "{r.SCORER_PINS[r.PINS_INDEX]}"' in wrapper
    index = json.loads((REPO / r.PINS_INDEX).read_text())
    assert index["pins_78b_sha256"] == r.SCORER_PINS[r.PINS_78B]
    assert {f"{r.SCORER_SETTINGS}/{k}": v for k, v in index["files"].items()} == {
        k: v for k, v in r.SCORER_PINS.items() if k.startswith(r.SCORER_SETTINGS) and k not in (r.PINS_INDEX, r.PINS_78B)}
    assert r.SCORER_PINS[r.ANCHOR_SCRIPT] == "5a686a82eb80d0a6da3f4f232b31bcda7c7840ced0038f666fe2a0e4a4d34146"   # Gate B's pin
    # the committed settings' own waits, read the way the wrapper reads them (scorers_78b.null_pins)
    for fam in FAMILIES:
        docs = {s: json.loads((REPO / f"{r.SCORER_SETTINGS}/{s}__{fam}.json").read_text())
                for s in ("make_untuned_answers", "representation_pass", "representation_pools", "score_l1_larf",
                          "score_classifier")}
        assert r.wrapper_settings_waits("untuned_answers", docs) == []
        assert [p for p, _ in r.wrapper_settings_waits("l1_scan", docs)] == ["score_l1_larf: pins.anchor_bank_sha256"]
        assert [p for p, _ in r.wrapper_settings_waits("classifier", docs)] == [
            "score_classifier: pins.anchor_bank_sha256", "score_classifier: pins.recipe_sha256"]
        assert [p for p, _ in r.wrapper_settings_waits("rep_pass", docs)] == [
            "representation_pass: pins.anchor_bank_sha256", "representation_pass: pins.recipe_sha256"]


def test_a_pin_filled_in_pins_78b_but_not_in_the_settings_still_refuses(so):
    w = so
    w.pack(*stand_in_lists(w))
    w.init([ANCHOR])
    anchor_done(w, f"{w.family}-sc-1")
    w.fill(anchor=True, settings=False)                  # pins_78b.json filled, the settings the wrapper reads still null
    with pytest.raises(SystemExit, match="the scorer layer's settings wait for 1 pin"):
        w.init([{"kind": "l1_scan"}], amount=None, dry_run=True)
    w.fill(anchor=True)
    assert w.init([{"kind": "l1_scan"}], amount=None, dry_run=True)["pods"][0]["kind"] == "l1_scan"


def test_the_release_and_the_pack_check_the_code_the_s78_config_and_a_unit_folder(so):
    w = so
    w.pack(*stand_in_lists(w))
    w.init([ANCHOR])
    anchor_done(w, f"{w.family}-sc-1")
    w.fill(anchor=True, recipe_s=True)
    right = w.s78["config_sha256"]
    w.config[w.s78["path"]] = hx("another config")      # the engine hashes the S_78 file to another value
    with pytest.raises(SystemExit, match="is not RECIPE_S's pin"):
        w.pack(*stand_in_lists(w), dry_run=True)
    w.config[w.s78["path"]] = right
    w.pack(*stand_in_lists(w), ("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())))
    w.config[w.s78["path"]] = hx("another config")
    with pytest.raises(SystemExit, match="is not RECIPE_S's pin"):
        w.init([{"kind": "classifier"}])
    w.config[w.s78["path"]] = right
    rel = "scripts/stage1/score_classifier.py"          # a code pin that is not the packed file's (a later kit pin)
    w.mp.setitem(w.rules.SCORER_PINS, rel, hx("another script"))
    with pytest.raises(SystemExit, match=f"the packed {rel} is not at its pin"):
        w.init([{"kind": "classifier"}])
    w.mp.setitem(w.rules.SCORER_PINS, rel, sha(w.repo / rel))
    host = w.init([{"kind": "classifier"}])["released"][0]
    assert w.plan()["hosts"][host]["jobs"][0]["recipe_s78"] == w.s78
    # a unit-folder input (the retrain's unit for A1's pass): its COMPLETE.json must have the pin, every file packed
    unit = w.retrain_unit()
    w.fill(retrain=sha(unit))
    with pytest.raises(SystemExit, match="not a unit folder whose COMPLETE.json has its pin"):
        w.pack(("retrain_unit", unit.parent.parent, sha(unit)), dry_run=True)
    (unit.parent / "COMPLETE.json").write_text("{}")
    with pytest.raises(SystemExit, match="not a unit folder whose COMPLETE.json has its pin"):
        w.pack(("retrain_unit", unit.parent, w.pins78()["families"][w.family]["a1_attributes_unit"]["retrain_complete_sha256"]),
               dry_run=True)
    unit = w.retrain_unit()
    w.pack(*stand_in_lists(w), ("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())), ("retrain_unit", unit.parent, sha(unit)))
    sealed = json.loads((w.root / "setup" / "packed-stage1-X" / "sealed-files.json").read_text())
    base = sealed["inputs"]["retrain_unit"]
    assert base == "inputs/retrain_unit/1101-a0-retrain-a1" and sealed["files"][f"{base}/COMPLETE.json"] == sha(unit)
    assert sealed["files"][f"{base}/states/e1/state.json"] == sha(unit.parent / "states/e1/state.json")


def test_the_runner_crashes_an_untuned_pass_without_its_pool(so, monkeypatch):
    w = so
    w.pack(*stand_in_lists(w))
    got = w.init([ANCHOR, UNTUNED])
    pod = ScPod(w, monkeypatch, got["released"][1], no_pool=True)
    assert pod.main() == 1
    assert pod.done()["jobs"][0]["why"] == "the S3 call wrote no s3_orig.pool.json"


def test_the_runner_checks_the_s78_config_on_the_pod(so, monkeypatch):
    w = so
    w.pack(*stand_in_lists(w))
    got = w.init([ANCHOR])
    anchor_done(w, got["released"][0])
    w.fill(anchor=True, recipe_s=True)
    w.pack(*stand_in_lists(w), ("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())))
    host = w.init([{"kind": "classifier"}])["released"][0]
    pod = ScPod(w, monkeypatch, host)
    pod.configs[str(pod.root / w.s78["path"])] = hx("another config")    # the pod's engine hashes S_78 otherwise
    with pytest.raises(AssertionError, match="the S_78 config differs from its pin"):
        pod.main()


def test_the_runner_refuses_a_host_whose_engine_is_not_a_pinned_one(so, monkeypatch):
    """G4 and A13 on the pod: the host's engine_sha256 must be its engine's pin (X; Y only once ENGINE_Y is filled)."""
    w = so
    w.pack(*stand_in_lists(w))
    host = w.init([ANCHOR])["released"][0]
    pod = ScPod(w, monkeypatch, host)
    plan = json.loads((pod.root / "plan.json").read_text())
    for engine, digest in (("X", "0" * 64), ("Y", Y)):  # another X identity; engine Y while ENGINE_Y is null
        plan["hosts"][host].update(engine=engine, engine_sha256=digest)
        for job in plan["hosts"][host]["jobs"]:
            job["engine"] = engine
        write(pod.root / "plan.json", plan)
        with pytest.raises(AssertionError, match="not a pinned engine"):
            pod.main()
    assert not [a for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]



# ===== 6. round 4b: the core verifier's D1-D8 and PP17 / PP18 ======================================================
def oext_inputs(w) -> list:
    return [("oext_bank", w.oext("bank"), sha(w.oext("bank"))), ("oext_record", w.oext("record"), sha(w.oext("record")))]


def receipts(pod) -> list:
    return [a[5:] for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]


def test_c0_is_unitless_and_its_outputs_are_hashed_under_its_job_folder_with_the_lean_jobs_real_layout(so, monkeypatch):
    """PP18 (the core verifier's D1): c0 is unitless; B17's lean job writes OUT/train (an engine unit), OUT/lean and
    OUT/c0_record.json under job-I/c0 (R: scripts/stage1_s1/lean_eval_job.py:42, :147), never OUT/COMPLETE.json. The
    runner hashes every file there (no engine verify: no unit is recorded), names c0_record.json's SHA-256, and a lean
    job that wrote no record is a crash; record-done keeps it unitless (the light pull leaves the states)."""
    w = so
    w.fill(oext=True, c0=True)
    w.pack(*stand_in_lists(w), *oext_inputs(w), ("source_complete:R:1101", w.c0_source(), sha(w.c0_source())))
    host = w.init([{"kind": "c0"}])["released"][0]
    pod = ScPod(w, monkeypatch, host, no_c0_record=True)
    assert pod.main() == 1
    assert pod.done()["jobs"][0]["status"] == "crashed" and pod.done()["jobs"][0]["why"] == "the lean job wrote no c0_record.json"
    shutil.rmtree(pod.root)
    pod = ScPod(w, monkeypatch, host)
    assert pod.main() == 0
    rec = pod.done()["jobs"][0]
    assert rec["status"] == "complete" and "unit" not in rec and "complete_sha256" not in rec and "verified" not in rec
    out = rec["outputs"]
    for rel in ("job-0/c0/c0_record.json", "job-0/c0/train/COMPLETE.json", "job-0/c0/lean/COMPLETE.json",
                "job-0/c0/lean/sealed/answers.json", "job-0/c0/train/states/e1/adapter.safetensors"):
        assert out[rel] == sha(pod.root / rel), rel
    assert rec["sc"] == {"kind": "c0", "c0_record_sha256": out["job-0/c0/c0_record.json"]}
    assert not [a for a in pod.ran if "verify" in a]                     # unitless: nothing to verify (PP18)
    assert [c[-1] if c[0] != "venv/bin/python" else c[2] for c in receipts(pod)][1] == w.r78.C0_SCRIPT
    assert not any(t in json.dumps(pod.done()) for t in SENTINELS)
    tree = w.root / "retrieved" / host / "tree"
    shutil.copytree(pod.root, tree)
    (tree / "job-0/c0/train/states/e1/adapter.safetensors").unlink()   # the light pull leaves model states on the pod
    got = w.tool.record_done(host)
    summary = got["scorer_block"][0]
    assert summary["c0_record_sha256"] == out["job-0/c0/c0_record.json"] and "complete_sha256" not in summary
    job = w.plan()["hosts"][host]["jobs"][0]
    assert job["unit"] is None and job["complete_sha256"] is None and job["states_on_pod"] == 1
    assert job["scorer_record"] == summary and not any(t in json.dumps(got) for t in SENTINELS)
    # record-done refuses a c0 record that names a unit or no record hash
    with pytest.raises(SystemExit, match="unitless"):
        w.done(host, outputs={"job-0/c0/c0_record.json": out["job-0/c0/c0_record.json"]}, unit="job-0/c0/train",
               complete_sha256=out["job-0/c0/train/COMPLETE.json"], sc={"kind": "c0", "c0_record_sha256": out["job-0/c0/c0_record.json"]})
    with pytest.raises(SystemExit, match="names no hashed job-0/c0/c0_record.json"):
        w.done(host, outputs={}, sc={"kind": "c0", "c0_record_sha256": out["job-0/c0/c0_record.json"]})


def unit_run(w, monkeypatch, tmp_path, kind: str, verify_exit: int = 0, side: dict | None = None,
             regen: dict | None = None, tamper: bool = False, oext_writes: bool = True):
    """run_sc_job of one unit kind on a synthetic pod folder (the real sc_commands; a fake process runner that writes
    the engine's unit, and the engine's verify exiting ``verify_exit``). Returns (record, calls, root)."""
    runner = load_by_path(f"jr78_unit_{kind}", w.root / "setup" / "job_runner_stage1.py")
    fam = w.family
    s78 = {"path": "experiments/safety_selection/configs/study-kt-olmo2-7b-s78-test.json", "config_sha256": hx("s78")}
    monkeypatch.setitem(w.r78.RECIPE_S, fam, s78["config_sha256"])
    root = tmp_path / "unit-pod"
    side_doc = side or {"checkpoints": {"q": {"adapter_fingerprint": hx("q"), "optimizer_fingerprint": hx("q-opt")},
                                        "e1": {"adapter_fingerprint": hx("e1"), "optimizer_fingerprint": hx("e1-opt")}},
                        "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("man")}, "evaluation": {"u": 0.73}}
    side_rel = "inputs/side_complete-a0-1101/COMPLETE.json"
    write(root / side_rel, side_doc)
    inputs = {"anchor_bank": "inputs/anchor_bank/a.json", "retrain_unit": "inputs/retrain_unit/1101-a0-retrain-a1",
              "oext_bank": "inputs/oext_bank/b.json", "oext_record": "inputs/oext_record/r.json",
              "side_complete:a0:1101": side_rel}
    pins = {"anchor_bank": hx("bank"), "retrain_unit": hx("unit"), "oext_bank": hx("ob"), "oext_record": hx("or"),
            "side_complete:a0:1101": sha(root / side_rel)}
    files = {rel: pins[n] for n, rel in inputs.items() if n != "retrain_unit"}
    files["inputs/retrain_unit/1101-a0-retrain-a1/COMPLETE.json"] = pins["retrain_unit"]
    doc = {"files": files, "inputs": inputs}
    if tamper:                                           # the side unit's file changed after its pin was taken
        write(root / side_rel, {**side_doc, "complete": "changed after its pin"})
    recipe = "B" if kind == "o_only_with_regenerate" else "S"
    engine = "X" if kind == "o_only_with_regenerate" else "Y"
    job = {"kind": kind, "arm": "a0", "seed": 1101, "recipe": recipe, "engine": engine,
           "inputs": {n: pins[n] for n in w.rules.sc_input_names(kind, 1101)}}
    if recipe == "S":
        job["recipe_s78"] = dict(s78)
    if kind == "a1_pass":
        job["groups"] = [f"g-{u:016x}" for u in range(8)]
    calls = []
    regen_doc = regen or {"complete": True, "checkpoints": side_doc["checkpoints"], "identity": side_doc["identity"]}

    def fake(args, **kwargs):
        calls.append(list(args))
        if args[:2] != ["python3", "process_receipt.py"]:
            return subprocess.CompletedProcess(args, verify_exit if "verify" in args else 0, "names only", "")
        argv = args[5:]
        out = root / argv[argv.index("--out") + 1]
        if "make-job" in argv:
            write(out, {"job": "synthetic"})
        elif w.r78.OEXT_UNIT_SCRIPT in argv:
            if oext_writes:
                write(out / "oext_record.json", {"kind": "oext (synthetic)"})
        else:
            write(out / "COMPLETE.json", regen_doc)
            write(out / "states" / "e1" / "state.json", {"adapter_fingerprint": regen_doc["checkpoints"]["e1"]["adapter_fingerprint"]})
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(runner.subprocess, "run", fake)
    plan = sc_plan(w, job, engine)
    rec = runner.run_sc_job(plan, "h", 0, root, {}, {}, doc)
    return rec, calls, root, runner


@pytest.mark.parametrize("kind", ["retrain", "a1_pass", "o_only_with_regenerate"])
@pytest.mark.parametrize("verify_exit", [0, 1])
def test_every_unit_the_scorer_runner_records_is_verified_by_the_engine(so, monkeypatch, tmp_path, kind, verify_exit):
    """The core verifier's D2: the retrain, A1's pass and o_only_with_regenerate's regenerated unit are each checked by
    `ENGINE verify --run UNIT --prepared PREPARED` right after the step that writes them (run_job's form); a non-zero
    exit is a crash (and o_only_with_regenerate then runs no acceptance and no O-ext pass)."""
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, kind, verify_exit)
    unit = {"retrain": "rescore/1101-a0-retrain-a1", "a1_pass": "rescore/1101-attributes-a1",
            "o_only_with_regenerate": "round1/1101-a0-regen-a1"}[kind]
    verify = [c for c in calls if "verify" in c]
    assert verify == [[*runner.ENGINE, "verify", "--run", unit, "--prepared", runner.PREPARED]]
    steps = [c[3] for c in calls if c[:2] == ["python3", "process_receipt.py"]]
    assert calls.index(verify[0]) == len([n for n in steps if not n.endswith("-oext")])   # right after the unit's step
    assert rec["unit"] == unit and rec["complete_sha256"] == sha(root / unit / "COMPLETE.json")
    assert rec["verified"] == {"exit": verify_exit, "tail": "names only"}
    if verify_exit:
        assert rec["status"] == "crashed" and rec["why"] == "the unit's verify failed"
        assert not [n for n in steps if n.endswith("-oext")] and not (root / "job-0" / runner.ACCEPT_FILE).exists()
    else:
        assert rec["status"] == "complete"
        assert ("fingerprints" in rec["sc"]) is (kind != "a1_pass")
        assert [n for n in steps if n.endswith("-oext")] == (["job-0-oext"] if kind == "o_only_with_regenerate" else [])


@pytest.mark.parametrize("field, side_change, regen_change", [
    (None, {}, {}),
    ("e1.adapter_fingerprint", {"e1": {"adapter_fingerprint": hx("another e1")}}, {}),
    ("q.optimizer_fingerprint", {}, {"q": {"optimizer_fingerprint": hx("another q-opt")}}),
    ("e1.optimizer_fingerprint", {}, {"e1": {"optimizer_fingerprint": hx("another e1-opt")}}),
    ("identity.training_identity", {}, {"identity": {"training_identity": hx("another identity")}}),
    ("identity.manifest_sha256", {"identity": {"manifest_sha256": hx("another manifest")}}, {}),
])
def test_o_only_with_regenerate_checks_the_regenerated_unit_against_the_side_units_fingerprints(
        so, monkeypatch, tmp_path, field, side_change, regen_change):
    """PP17 (the 1B J2 / LN-12 link): every q and e1 adapter and optimizer fingerprint the side unit lists and its
    training identity and prepared manifest must equal the regenerated unit's; the record holds those hashes only. A
    unit that differs is complete with acceptance false and reason LS-04, and its O-ext pass never runs."""
    def merged(change):
        doc = {"checkpoints": {"q": {"adapter_fingerprint": hx("q"), "optimizer_fingerprint": hx("q-opt")},
                               "e1": {"adapter_fingerprint": hx("e1"), "optimizer_fingerprint": hx("e1-opt")}},
               "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("man")}}
        for key, sub in change.items():
            (doc["identity"] if key == "identity" else doc["checkpoints"][key]).update(sub)
        return doc
    side, regen = merged(side_change), {"complete": True, **merged(regen_change)}
    side["evaluation"] = {"u": float(SENTINELS[2])}                    # never read (an outcome field of COMPLETE.json)
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", 0, side, regen)
    accept = json.loads((root / "job-0" / runner.ACCEPT_FILE).read_text())
    assert sorted(accept["fields"]) == ["e1.adapter_fingerprint", "e1.optimizer_fingerprint", "identity.manifest_sha256",
                                        "identity.training_identity", "q.adapter_fingerprint", "q.optimizer_fingerprint"]
    assert [f for f, v in accept["fields"].items() if not v["equal"]] == ([field] if field else [])
    assert accept["kind"] == "stage1-78b regeneration acceptance" and accept["seed"] == 1101
    assert SENTINELS[2] not in json.dumps(accept) and SENTINELS[2] not in json.dumps(rec)
    steps = [c[3] for c in calls if c[:2] == ["python3", "process_receipt.py"]]
    assert rec["status"] == "complete" and rec["sc"]["acceptance"] is (field is None)
    assert rec["outputs"]["job-0/" + runner.ACCEPT_FILE] == sha(root / "job-0" / runner.ACCEPT_FILE) == \
        rec["sc"]["acceptance_record_sha256"]
    if field is None:
        assert steps[-1] == "job-0-oext" and rec["acceptance"] is True and "reason" not in rec
        assert rec["outputs"]["job-0/oext/oext_record.json"] == sha(root / "job-0/oext/oext_record.json")
    else:
        assert "job-0-oext" not in steps and rec["acceptance"] is False and rec["reason"] == "LS-04"
        assert not any(k.startswith("job-0/oext/") for k in rec["outputs"])


def test_o_only_with_regenerate_crashes_on_a_changed_side_unit_or_an_empty_oext_pass(so, monkeypatch, tmp_path):
    """The acceptance re-hashes the packed side unit's COMPLETE.json against its pin before reading it (a changed file
    is a crash, nothing accepted); an O-ext pass that wrote nothing is a crash."""
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", tamper=True)
    assert rec["status"] == "crashed" and "differs from its pin" in rec["why"]
    assert not (root / "job-0" / runner.ACCEPT_FILE).exists() and "job-0-oext" not in [c[3] for c in calls if len(c) > 3]
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path / "b", "o_only_with_regenerate", oext_writes=False)
    assert rec["status"] == "crashed" and rec["why"] == "the O-ext pass wrote no output"


def test_o_only_with_regenerate_end_to_end_waits_on_oext_and_records_its_acceptance(so, monkeypatch):
    """PP17 through the real route: planned only once OEXT_78B is filled (it waits on it, as o_only does), on engine
    X, one pod per reused seed with its side unit's COMPLETE.json packed at ruling 7's pin; the pod regenerates,
    verifies, accepts, then runs the O-ext pass on the regenerated e1 state; record-done prints the verdict."""
    w = so
    with pytest.raises(SystemExit, match="OEXT_78B waits for"):
        w.init([REGEN], amount=None, dry_run=True)
    w.fill(oext=True)
    side = w.side_unit(1101)
    with pytest.raises(SystemExit, match="'side_complete:a0:1101''s SHA-256 is not its pin"):
        w.pack(("side_complete:a0:1101", side, hx("not the side unit")))
    dry = w.init([REGEN], amount=None, dry_run=True)
    assert dry["pods"][0]["inputs"] == {"side_complete:a0:1101": sha(side), "oext_bank": sha(w.oext("bank")),
                                        "oext_record": sha(w.oext("record"))}
    assert dry["pods"][0]["engine"] == "X" and dry["pods"][0]["cap_hours"] == 4.5
    w.pack(*oext_inputs(w), ("side_complete:a0:1101", side, sha(side)))
    host = w.init([REGEN])["released"][0]
    pod = ScPod(w, monkeypatch, host)
    assert pod.main() == 0
    rec = pod.done()["jobs"][0]
    assert rec["status"] == "complete" and rec["unit"] == "round1/1101-a0-regen-a1" and rec["verified"]["exit"] == 0
    assert rec["acceptance"] is True and rec["sc"]["acceptance"] is True
    names = [a[3] for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]
    verify = next(i for i, a in enumerate(pod.ran) if "verify" in a)
    oext = next(i for i, a in enumerate(pod.ran) if a[:2] == ["python3", "process_receipt.py"] and a[3] == "job-0-oext")
    assert names == ["job-0-make-job", "job-0-run-one", "job-0-oext"] and verify < oext
    oext_argv = pod.ran[oext][5:]
    assert oext_argv[oext_argv.index("--run") + 1] == rec["unit"] and oext_argv[oext_argv.index("--checkpoint") + 1] == "e1"
    assert not any(t in json.dumps(pod.done()) for t in SENTINELS)
    tree = w.root / "retrieved" / host / "tree"
    shutil.copytree(pod.root, tree)
    got = w.tool.record_done(host)["scorer_block"][0]
    assert got["acceptance"] is True and got["oext_run"] is True and got["verified_exit"] == 0
    assert got["complete_sha256"] == rec["complete_sha256"]
    # LS-04 on the pod: the regenerated unit differs (its q adapter); complete, acceptance false, no O-ext pass
    shutil.rmtree(pod.root)
    differs = {"kind": "COMPLETE (synthetic)", "complete": True,
               "checkpoints": {"e1": {"adapter_fingerprint": hx("e1"), "optimizer_fingerprint": hx("e1-opt")},
                               "q": {"adapter_fingerprint": hx("another q"), "optimizer_fingerprint": hx("q-opt")}},
               "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("man")}}
    pod = ScPod(w, monkeypatch, host, unit_complete=differs)
    assert pod.main() == 0
    rec = pod.done()["jobs"][0]
    assert rec["status"] == "complete" and rec["acceptance"] is False and rec["reason"] == "LS-04"
    assert "job-0-oext" not in [a[3] for a in pod.ran if a[:2] == ["python3", "process_receipt.py"]]
    shutil.rmtree(tree)
    shutil.copytree(pod.root, tree)
    got = w.tool.record_done(host)["scorer_block"][0]
    assert got["acceptance"] is False and got["oext_run"] is False
    assert w.plan()["hosts"][host]["jobs"][0]["reason"] == "LS-04"
    with pytest.raises(SystemExit, match="names no acceptance verdict"):
        w.done(host, unit=rec["unit"], complete_sha256=rec["complete_sha256"], verified={"exit": 0, "tail": ""},
               sc={"kind": "o_only_with_regenerate", "fingerprints": rec["sc"]["fingerprints"],
                   "acceptance_record_sha256": rec["sc"]["acceptance_record_sha256"]})
    with pytest.raises(SystemExit, match="names no acceptance verdict"):     # a verdict that contradicts the reason
        w.done(host, unit=rec["unit"], complete_sha256=rec["complete_sha256"], verified={"exit": 0, "tail": ""},
               sc={"kind": "o_only_with_regenerate", "fingerprints": rec["sc"]["fingerprints"], "acceptance": True,
                   "acceptance_record_sha256": rec["sc"]["acceptance_record_sha256"]}, reason="LS-04")


def test_the_anchor_bank_and_s3_orig_pins_must_be_this_copys_recorded_outputs(so):
    """The core verifier's D5: a kind that reads the anchor bank (or the s3_orig pool) is planned only when the pin
    is the SHA-256 a complete anchor (untuned) job of this copy's plan recorded; another file's hash refuses."""
    w = so
    w.pack(*stand_in_lists(w))
    host = f"{w.family}-sc"
    w.init([ANCHOR, UNTUNED])
    other = write(w.repo / "tmp" / "anchors" / "another-family-anchors.json", {"kind": "another anchor file"})
    anchor_done(w, f"{host}-1", bank=other)               # the job recorded ANOTHER file than the pin names
    w.fill(anchor=True, recipe_s=True)
    for kind in ("l1_scan", "classifier"):
        with pytest.raises(SystemExit, match="the ANCHOR_BANK pin is not the anchor_file_sha256"):
            w.init([{"kind": kind}], amount=None, dry_run=True)
    # with the recorded anchor file as the pin it plans; the s3_orig pool is bound the same way
    w.fill(anchor=False, settings=True)
    doc = w.pins78()
    doc["families"][w.family]["anchor_bank_sha256"] = sha(other)
    write(w.repo / w.rules.PINS_78B, doc)
    w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_78B, sha(w.repo / w.rules.PINS_78B))
    for script in ("representation_pass", "score_classifier", "score_l1_larf"):
        rel = f"{w.rules.SCORER_SETTINGS}/{script}__{w.family}.json"
        s = json.loads((w.repo / rel).read_text())
        s["pins"]["anchor_bank_sha256"] = sha(other)
        write(w.repo / rel, s)
        w.mp.setitem(w.rules.SCORER_PINS, rel, sha(w.repo / rel))
    index = json.loads((w.repo / w.rules.PINS_INDEX).read_text())
    index["pins_78b_sha256"] = w.rules.SCORER_PINS[w.rules.PINS_78B]
    write(w.repo / w.rules.PINS_INDEX, index)
    w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_INDEX, sha(w.repo / w.rules.PINS_INDEX))
    assert w.init([{"kind": "l1_scan"}], amount=None, dry_run=True)["pods"][0]["kind"] == "l1_scan"
    w.s3_orig = lambda: write(w.repo / "tmp" / "untuned" / "another.pool.json", {"kind": "another pool"})
    untuned_done(w, f"{host}-2")                          # the untuned job recorded ANOTHER pool
    del w.s3_orig
    w.fill(s3_orig=True, settings=False)
    with pytest.raises(SystemExit, match="the S3_ORIG_POOL pin is not the s3_orig_pool_sha256"):
        w.init([{"kind": "rep_pass"}], amount=None, dry_run=True)


@pytest.mark.parametrize("oext, match", [
    ({"files": {"scripts/stage1_s1/oext_unit.py": hx("s")}}, "keys are not exactly files and inputs"),
    ({"files": {"scripts/stage1_s1/oext_unit.py": hx("s")}, "inputs": {"oext_bank": hx("b")}}, "inputs does not hold"),
    ({"files": {"experiments/x.py": hx("s")}, "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}}, "under scripts/"),
    ({"files": {"scripts/../x.py": hx("s")}, "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}}, "under scripts/"),
    ({"files": {"scripts/x.py": "not a hash"}, "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}}, "is not a SHA-256"),
    ({"files": {}, "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}}, "non-empty mapping"),
    ({"files": {"scripts/x.py": hx("s")}, "inputs": {"oext_bank": hx("b"), "oext_record": "x"}}, "an input is not"),
    ({"files": {"scripts/x.py": hx("s")}, "inputs": {"oext_bank": hx("b"), "oext_record": hx("r")}, "x": 1}, "keys are not"),
])
def test_oext_78b_takes_its_documented_form_only(so, monkeypatch, oext, match):
    """The core verifier's D6: OEXT_78B[family] is {files: {path under scripts/: SHA-256}, inputs: {oext_bank,
    oext_record}}; any other form refuses at sc_pin_values (so at planning and at the pack), naming why."""
    w = so
    monkeypatch.setitem(w.r78.OEXT_78B, w.family, oext)
    with pytest.raises(w.r78.Refused, match=match):
        w.r78.sc_pin_values(w.family, w.pins78())
    with pytest.raises(SystemExit, match="OEXT_78B"):
        w.init([{"kind": "o_only"}], amount=None, dry_run=True)


def test_an_oext_kind_refuses_when_oext_78b_does_not_list_its_script(so, monkeypatch):
    """HM14: o_only and o_only_with_regenerate need OEXT_UNIT_SCRIPT, c0 needs C0_SCRIPT, among OEXT_78B's files."""
    w = so
    assert w.r78.OEXT_WRAPPER_COMMANDS["c0"] == "lean" and w.r78.OEXT_WRAPPER_COMMANDS["o_only"] == "unit"   # R1 K1 fix
    w.fill(oext=True, c0=True)
    full = w.r78.OEXT_78B[w.family]
    for drop, kinds in ((w.r78.OEXT_UNIT_SCRIPT, ({"kind": "o_only"}, REGEN)), (w.r78.C0_SCRIPT, ({"kind": "c0"},))):
        kept = {k: v for k, v in full["files"].items() if k != drop} or {"scripts/stage1_s1/oext_eval.py": "e" * 64}
        monkeypatch.setitem(w.r78.OEXT_78B, w.family, {"files": kept,      # R1 K1: one wrapper path; keep files non-empty
                                                       "inputs": full["inputs"]})
        for job in kinds:
            with pytest.raises(SystemExit, match=f"do not pin the wrapper {drop}"):   # R1 K1 fix: GXB R-5's form check comes first
                w.init([job], amount=None, dry_run=True)
    monkeypatch.setitem(w.r78.OEXT_78B, w.family, full)
    for kind in ("o_only", "o_only_with_regenerate", "c0"):          # R1 K1 fix: each O-ext kind packs OEXT_78B's files
        assert w.rules.scorer_code(kind) == sorted(full["files"]), kind
    assert len(w.init([{"kind": "o_only"}, REGEN, {"kind": "c0"}], amount=None, dry_run=True)["pods"]) == 3


def test_record_done_needs_the_anchor_files_hash_and_a_complete_kind_is_never_planned_again(so):
    """HM4: a complete anchor job that names no anchor file SHA-256 refuses at record-done. HM8: a kind recorded
    complete in this copy's plan is not planned again (A8: one pod per job)."""
    w = so
    w.pack(*stand_in_lists(w))
    host = w.init([ANCHOR])["released"][0]
    a = write(w.root / "retrieved" / host / "tree" / "job-0" / "anchors" / "anchors.json", {"answers": SENTINELS[0]})
    with pytest.raises(SystemExit, match="names no anchor file SHA-256"):
        w.done(host, outputs={"job-0/anchors/anchors.json": sha(a)}, sc={"kind": "anchor"})
    anchor_done(w, host)
    with pytest.raises(SystemExit, match=r"already planned \(complete\)"):
        w.init([ANCHOR], amount=None, dry_run=True)


def test_the_runner_crashes_an_anchor_job_without_its_sealed_record(so, monkeypatch):
    """HM5: the anchor job is complete only with anchors.json AND anchors.sealed.json (A1: S_78 needs the sealed one)."""
    w = so
    w.pack(*stand_in_lists(w))
    host = w.init([ANCHOR])["released"][0]
    pod = ScPod(w, monkeypatch, host, no_sealed_anchor=True)
    assert pod.main() == 1
    assert pod.done()["jobs"][0]["why"] == "the anchor job wrote no anchors.json or anchors.sealed.json"


def test_record_done_refuses_a_unit_kind_without_its_unit_or_its_engine_verify(so):
    """D2 and D8 on the Mac: a complete retrain, a1_pass or o_only_with_regenerate record must name its unit, its
    COMPLETE.json SHA-256 and the engine's verify at exit 0 (a1_pass is a unit kind, not unitless)."""
    w = so
    assert "a1_pass" not in w.rules.UNITLESS_KINDS and "c0" in w.rules.UNITLESS_KINDS
    assert w.tool.SC_UNIT_KINDS == ("retrain", "a1_pass", "o_only_with_regenerate")
    runner = load_by_path("jr78_units", w.root / "setup" / "job_runner_stage1.py")
    assert runner.SC_UNIT_KINDS == w.tool.SC_UNIT_KINDS


def test_the_backup_checks_a1_pass_by_its_unit_and_a_scorer_unit_jobs_outputs(so):
    """D8: backup_records_stage1.py treats a1_pass as a unit job (its sealed unit at the recorded COMPLETE.json
    SHA-256), as the runner and record-done do; a scorer-block unit job's recorded outputs (o_only_with_regenerate's
    O-ext files and acceptance record) must be staged too."""
    w = so
    backup = load_by_path("backup_sc", w.root / "backup_records_stage1.py")
    tree = w.root / "retrieved" / "h" / "tree"
    attr = write(tree / "rescore" / "1101-attributes-a1" / "attributes.json", {"kind": "attributes (synthetic)"})
    unit = write(tree / "rescore" / "1101-attributes-a1" / "COMPLETE.json", {"files": {"attributes.json": sha(attr)}})
    regen = write(tree / "round1" / "1101-a0-regen-a1" / "COMPLETE.json", {"files": {}})
    oext = write(tree / "job-1" / "oext" / "oext_record.json", {"kind": "oext (synthetic)"})
    plan = {"hosts": {"h": {"block": "sc", "jobs": [
        {"kind": "a1_pass", "status": "complete", "unit": "rescore/1101-attributes-a1", "complete_sha256": sha(unit),
         "outputs": None},
        {"kind": "o_only_with_regenerate", "status": "complete", "unit": "round1/1101-a0-regen-a1",
         "complete_sha256": sha(regen), "outputs": {"job-1/oext/oext_record.json": sha(oext)}}]}}}
    staged = {f"units/h/{p.relative_to(tree)}": sha(p) for p in tree.rglob("*") if p.is_file()}
    missing = []
    backup.sealed_units(plan, ["h"], staged, missing)
    assert missing == []
    unit.write_text("{}")                                 # the sealed unit's COMPLETE.json differs from the record
    missing = []
    backup.sealed_units(plan, ["h"], {**staged, "units/h/rescore/1101-attributes-a1/COMPLETE.json": sha(unit)}, missing)
    assert missing == ["h: job 0's COMPLETE.json differs from plan.json's record"]
    write(unit, {"files": {"attributes.json": sha(attr)}})
    missing = []
    backup.sealed_units(plan, ["h"], {k: v for k, v in staged.items() if "oext" not in k}, missing)
    assert missing == ["h: job 1: 1 recorded output(s) not staged or changed"]



# ===== 7. round 4b: the pack's secret scan covers the named scorer inputs (the security verifier's D5) ==============
def test_the_pack_refuses_a_token_shaped_string_in_a_named_scorer_input(so, request):
    """inputs/ holds the scorer block's named inputs (anchor prompts, the 1B lists and pools, unit records): every
    non-binary file there is scanned at pack time; a hit refuses with the input's bundle path only (never the text),
    and nothing is packed. A model-weight file (.safetensors) is not scanned. The token-shaped string is built here
    (no real token). Every file that holds the string is removed when the test ends, pass or fail (K6, K5v-2)."""
    w = so
    fake = "hf_" + "Q7" * 17                              # 'hf_' + 34 characters: the HF token's shape, not a token
    items = stand_in_lists(w)
    name, path, _ = items[-1]
    request.addfinalizer(lambda: [f.unlink(missing_ok=True) for f in (
        path, w.repo / "tmp" / "w" / "adapter.safetensors", w.repo / "tmp" / "w" / "x.json")])
    assert name == "anchor_prompts"
    write(path, {"prompts": ["a synthetic prompt", fake]})
    doc = w.pins78()
    doc["shared"]["anchor_prompt_list_sha256"] = sha(path)
    write(w.repo / w.rules.PINS_78B, doc)
    w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_78B, sha(w.repo / w.rules.PINS_78B))
    index = json.loads((w.repo / w.rules.PINS_INDEX).read_text())
    index["pins_78b_sha256"] = w.rules.SCORER_PINS[w.rules.PINS_78B]
    write(w.repo / w.rules.PINS_INDEX, index)
    w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_INDEX, sha(w.repo / w.rules.PINS_INDEX))
    with pytest.raises(SystemExit) as info:
        w.pack(("anchor_prompts", path, sha(path)))
    text = str(info.value)
    assert text.startswith("a secret pattern is in 1 packed scorer input file(s): ['inputs/anchor_prompts/")
    assert fake not in text and "hf_" not in text
    assert not (w.root / "setup" / "packed-stage1-X").exists()
    pack = importlib.import_module("pack_setup")
    weights = write(w.repo / "tmp" / "w" / "adapter.safetensors", fake)
    clean = write(w.repo / "tmp" / "w" / "state.json", {"adapter_fingerprint": hx("e1")})
    pack.refuse_secrets({"inputs/retrain_unit/u/states/e1/adapter.safetensors": weights,
                         "inputs/retrain_unit/u/states/e1/state.json": clean}, {}, pack.DATA_PREFIXES)
    with pytest.raises(SystemExit, match=r"1 packed scorer input file\(s\): \['inputs/retrain_unit/u/x.json'\]"):
        pack.refuse_secrets({"inputs/retrain_unit/u/x.json": write(w.repo / "tmp" / "w" / "x.json", {"t": fake})}, {},
                            pack.DATA_PREFIXES)


# ===== 8. round 5 (K5): the core re-verifier's K4bcr-D1, D2 and D3 ===================================================
# D1: c0's expected e1 adapter fingerprint comes from the packed source unit's COMPLETE.json (the 1B @fingerprint form)
def c0_cmds(w, runner, tmp_path, source_doc, expect, change_after_pin=None):
    """job_commands of a c0 job whose packed source unit's COMPLETE.json is ``source_doc`` (pinned by its bytes), and
    whose plan carries ``expect`` (C0_SOURCE's e1_fingerprint); ``change_after_pin`` rewrites the file after its pin
    was taken."""
    rel = "inputs/source_complete-R-1101/COMPLETE.json"
    src = write(tmp_path / rel, source_doc)
    pins = {"source_complete:R:1101": sha(src), "oext_bank": hx("ob"), "oext_record": hx("or")}
    inputs = {"source_complete:R:1101": rel, "oext_bank": "inputs/oext_bank/b.json", "oext_record": "inputs/oext_record/r.json"}
    doc = {"files": {inputs[n]: pins[n] for n in pins}, "inputs": inputs}
    if change_after_pin is not None:
        write(src, change_after_pin)
    job = {"kind": "c0", "arm": "R", "seed": 1101, "recipe": "B", "engine": "X", "inputs": pins,
           "edit": {"sha256": hx("rd1"), "path": "x"}, "expect_fingerprint": expect}
    return [c for _, c in runner.job_commands(sc_plan(w, job), "h", 0, tmp_path, {}, doc)]


def test_k5_d1_c0_reads_its_expected_fingerprint_from_the_packed_source_unit_and_refuses_another(so, tmp_path):
    """K4bcr-D1: the c0 command passes the e1 adapter fingerprint read from the packed source unit's COMPLETE.json,
    after re-hashing the file against its pin (the stage-1 kit's @fingerprint:source_complete:R:1101,
    R: runkit/stage1-olmo/setup/job_runner_stage1.py:517, :770-776); a plan value that differs from it (a typing
    error in the lead's C0_SOURCE step), a file changed after its pin, or a file with no e1 fingerprint refuses."""
    w = so
    good = {"kind": "COMPLETE (synthetic)", "checkpoints": {"e1": {"adapter_fingerprint": hx("the real e1")}},
            "evaluation": {"u": float(SENTINELS[2])}}
    runner = load_by_path("jr78_k5_c0", w.root / "setup" / "job_runner_stage1.py")
    cmds = c0_cmds(w, runner, tmp_path / "a", good, hx("the real e1"))
    lean = cmds[1]
    assert lean[lean.index("--expect-adapter-fingerprint") + 1] == hx("the real e1")
    with pytest.raises(runner.Unrunnable, match=r"job 0 \(c0\): the packed source unit's e1 adapter fingerprint is not "
                                                r"the plan's expected one \(C0_SOURCE\)"):
        c0_cmds(w, runner, tmp_path / "b", good, hx("a typo in the step"))
    with pytest.raises(runner.Unrunnable, match="the packed source unit's COMPLETE.json is missing or differs from its pin"):
        c0_cmds(w, runner, tmp_path / "c", good, hx("the real e1"),
                change_after_pin={**good, "checkpoints": {"e1": {"adapter_fingerprint": hx("another e1")}}})
    with pytest.raises(runner.Unrunnable, match="lists no e1 adapter fingerprint"):
        c0_cmds(w, runner, tmp_path / "d", {"kind": "COMPLETE (synthetic)", "checkpoints": {"q": {"adapter_fingerprint": hx("q")}}},
                hx("the real e1"))


def test_k5_d1_a_c0_pod_whose_c0_source_step_differs_from_the_packed_unit_runs_no_step(so, monkeypatch):
    """K4bcr-D1 through the real route, and R2 K2's K6v-4 (Part 2 §15 item 12): C0_SOURCE's complete_sha256 is the
    packed source file's, its e1_fingerprint a typing error made AFTER a clean pack. The release (inside init-block
    sc) now reads the packed source unit from the bundle and refuses on the Mac, writing nothing (before R2 K2 the
    route passed and only the pod refused). The pod-side layer stays: a plan whose expected fingerprint is edited after
    the release crashes the pod before any step (no lean job, so no false engine-X alarm from B17)."""
    w = so
    w.fill(oext=True, c0=True)
    w.pack(*stand_in_lists(w), *oext_inputs(w), ("source_complete:R:1101", w.c0_source(), sha(w.c0_source())))
    w.mp.setitem(w.r78.C0_SOURCE, w.family, {"complete_sha256": sha(w.c0_source()), "e1_fingerprint": hx("a typo")})
    with pytest.raises(SystemExit, match=r"c0's packed source unit's e1 adapter fingerprint is not C0_SOURCE's "
                                         r"e1_fingerprint now \(an edit of the pin after the pack, K6v-4\)"):
        w.init([{"kind": "c0"}])
    assert not (w.root / "plan.json").exists()
    w.mp.setitem(w.r78.C0_SOURCE, w.family, {"complete_sha256": sha(w.c0_source()), "e1_fingerprint": hx("e1-R-1101")})
    host = w.init([{"kind": "c0"}])["released"][0]
    plan = w.plan()
    plan["hosts"][host]["jobs"][0]["expect_fingerprint"] = hx("a typo")   # the pod-side layer alone
    w.mac.save_plan(plan)
    pod = ScPod(w, monkeypatch, host)
    assert pod.main() == 1
    rec = pod.done()["jobs"][0]
    assert rec["status"] == "crashed" and "is not the plan's expected one (C0_SOURCE)" in rec["why"]
    assert receipts(pod) == []                                         # no step ran
    shutil.rmtree(pod.root)                                            # the right value: the lean job gets it
    plan = w.plan()
    plan["hosts"][host]["jobs"][0]["expect_fingerprint"] = hx("e1-R-1101")
    w.mac.save_plan(plan)
    pod = ScPod(w, monkeypatch, host)
    assert pod.main() == 0
    lean = [a for a in receipts(pod) if w.r78.C0_SCRIPT in a][0]
    assert lean[lean.index("--expect-adapter-fingerprint") + 1] == hx("e1-R-1101")


# D2: the prior verifier's HM6 (output hashing follows links), HM7 (another family's receipt), HM13 (an empty pass)
def test_k5_d2_hm6_the_output_hashing_never_follows_a_symbolic_link(so, tmp_path):
    """HM6: hashed_outputs lists regular files only; a link in a job folder (to a file outside it, or a folder) is
    neither hashed nor recorded."""
    runner = load_by_path("jr78_k5_hm6", so.root / "setup" / "job_runner_stage1.py")
    root = tmp_path / "pod"
    real = write(root / "job-0" / "oext" / "oext_record.json", {"kind": "oext (synthetic)"})
    outside = write(tmp_path / "outside" / "secret-ish.json", {"kind": "a file outside the job folder"})
    (root / "job-0" / "oext" / "link.json").symlink_to(outside)
    (root / "job-0" / "oext" / "linked-folder").symlink_to(outside.parent, target_is_directory=True)
    got = runner.hashed_outputs(root, ["job-0/oext"])
    assert got == {"job-0/oext/oext_record.json": sha(real)}


def test_k5_d2_hm7_the_scorer_release_refuses_another_familys_packed_receipt(so):
    """HM7 (KD7): a packed stage1-X whose receipt names the other family refuses the scorer block's release."""
    w = so
    w.pack(*stand_in_lists(w))
    assert w.init([ANCHOR], [UNTUNED])["released"] == [f"{w.family}-sc-1"]
    anchor_done(w, f"{w.family}-sc-1")
    other = next(f for f in FAMILIES if f != w.family)
    path = w.root / "setup" / "packed-stage1-X" / "setup-receipt.json"
    receipt = json.loads(path.read_text())
    path.write_text(json.dumps({**receipt, "family": other}, indent=2) + "\n")
    with pytest.raises(SystemExit, match=rf"the packed stage1-X is {other}'s; this copy is {w.family}'s \(KD7\)"):
        w.tool.release("sc")
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    assert w.tool.release("sc")["released"] == [f"{w.family}-sc-2"]


def test_k5_d2_hm13_a_unitless_scorer_pass_that_wrote_nothing_is_a_crash(so, monkeypatch, tmp_path):
    """HM13: the theta0 O-ext pass (o_only, unitless; its last check is the only guard) that exits 0 and writes
    nothing is crashed, not complete with its cost ledger only."""
    w = so
    runner = load_by_path("jr78_k5_hm13", w.root / "setup" / "job_runner_stage1.py")
    pins = {"oext_bank": hx("ob"), "oext_record": hx("or")}
    inputs = {"oext_bank": "inputs/oext_bank/b.json", "oext_record": "inputs/oext_record/r.json"}
    doc = {"files": {inputs[n]: pins[n] for n in pins}, "inputs": inputs}
    job = {"kind": "o_only", "arm": "theta0", "seed": None, "recipe": "B", "engine": "X", "inputs": pins}
    for writes, status in ((False, "crashed"), (True, "complete")):
        root = tmp_path / f"pod-{writes}"

        def fake(args, **kwargs):
            argv = args[5:]
            if writes:
                write(root / argv[argv.index("--out") + 1] / "oext_record.json", {"kind": "oext (synthetic)"})
            return subprocess.CompletedProcess(args, 0, "", "")
        monkeypatch.setattr(runner.subprocess, "run", fake)
        rec = runner.run_sc_job(sc_plan(w, job), "h", 0, root, {}, {}, doc)
        assert rec["status"] == status, rec
        if not writes:
            assert rec["why"] == "the job wrote no output"
        else:
            assert list(rec["outputs"]) == ["job-0/oext/oext_record.json"]


# D3: the re-verifier's scratch tests S1-S6 (reports/k4b-core-scratch/test_k4bcr_scratch.py), adopted
def cents(x: float) -> float:
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def test_k5_s1_part1_every_seed_its_own_side_pin_and_the_need_by_hand(sw, capsys):
    """S1 (K4bcr-R8, PP17): part 1 of both families with every o_only_with_regenerate seed; each pod's side-unit pin is
    its own seed's KIT a0_units pin (the pins differ across seeds); guards, needs and caps by hand."""
    w = sw
    r78 = w.r78
    seeds = r78.sc_seeds(w.family, "o_only_with_regenerate")
    assert seeds == ([1101, 1102, 1103] if w.family == "olmo2-7b" else [1101, 1102])
    w.fill(oext=True, c0=True)
    sides = {s: w.side_unit(s, kind=f"COMPLETE (synthetic side unit {s})") for s in seeds}
    assert len({sha(p) for p in sides.values()}) == len(seeds)
    launch = [ANCHOR, UNTUNED, {"kind": "o_only"}] + [{"kind": "o_only_with_regenerate", "seed": s} for s in seeds] + \
        [{"kind": "c0"}]
    dry = w.init(launch, amount=None, dry_run=True)
    pods = dry["pods"]
    assert [p["kind"] for p in pods] == [j["kind"] for j in launch]
    for p in pods:
        assert p["engine"] == "X"                                     # PP16: all of part 1 is X-only
        assert p["guard_usd"] == cents(6 + 1.85 * p["cap_hours"])     # guard by hand
        assert p["need_usd_alone"] == cents(1.25 * p["guard_usd"])    # need alone by hand
    regen = [p for p in pods if p["kind"] == "o_only_with_regenerate"]
    for p, s in zip(regen, seeds):                                    # R8: each seed's pin is its own side unit's
        assert p["inputs"][f"side_complete:a0:{s}"] == sha(sides[s]) == r78.KIT[w.family]["a0_units"][s]["complete_sha256"]
        assert p["cap_hours"] == 4.5 and p["idle_storage"]["keeps_states"] is True
    caps = {p["kind"]: p["cap_hours"] for p in pods}
    assert caps == {"anchor": 2.25, "untuned_answers": 6.0, "o_only": 3.75, "o_only_with_regenerate": 4.5,
                    "c0": 4.25 if w.family == "olmo2-7b" else 4.5}
    base = cents(6 + 1.85 * sum(p["cap_hours"] for p in pods))         # one launch: the reserve + 1.85 x the caps
    assert dry["base_need_usd"] == base and dry["need_usd"] == cents(1.25 * base)
    kept = [p for p in pods if p["idle_storage"]["keeps_states"]]
    assert [p["kind"] for p in kept] == ["o_only_with_regenerate"] * len(seeds) + ["c0"]


def test_k5_s2_parts_2_and_3_in_a2_order_and_a1_pass_reads_the_recorded_anchor_file(sw, capsys):
    """S2 (K4bcr-R13, D5): parts 2 and 3 in A2's order for both families (caps, engines and needs by hand); with the
    anchor pin moved to another file after part 2, A1's pass refuses (its ANCHOR_BANK pin is not the recorded file)."""
    w = sw
    host = f"{w.family}-sc"
    w.pack(*stand_in_lists(w))
    w.init([ANCHOR, UNTUNED])
    other = write(w.repo / "tmp" / "anchors" / "another-anchors.json", {"kind": "another anchor file"})
    anchor_done(w, f"{host}-1")
    untuned_done(w, f"{host}-2")
    w.fill(anchor=True, recipe_s=True, s3_orig=True, engine_y=True)
    part2 = [{"kind": "l1_scan"}, {"kind": "classifier"}, {"kind": "rep_pass"}, {"kind": "retrain"}]
    dry2 = w.init(part2, amount=None, dry_run=True)
    assert [(p["kind"], p["engine"], p["cap_hours"]) for p in dry2["pods"]] == [
        ("l1_scan", "X", 4.75), ("classifier", "X", 3.25), ("rep_pass", "X", 4.75), ("retrain", "Y", 4.5)]
    base2 = cents(6 + 1.85 * (4.75 + 3.25 + 4.75 + 4.5))
    assert dry2["base_need_usd"] == base2 and dry2["need_usd"] == cents(1.25 * base2)
    w.pack(*stand_in_lists(w), ("anchor_bank", w.anchor_bank(), sha(w.anchor_bank())))
    y = w.root / "setup" / "packed-stage1-Y"
    write(y / "sealed-files.json", {"files": {w.s78["path"]: sha(w.repo / w.s78["path"])}, "inputs": {}})
    write(y / "setup-receipt.json", {"engine_sha256": Y, "family": w.family,
                                     "sealed_files_sha256": sha(y / "sealed-files.json")})
    retrain_host = w.init([{"kind": "retrain"}])["released"][0]
    unit = w.retrain_unit()
    tree = w.root / "retrieved" / retrain_host / "tree"
    shutil.copytree(unit.parent, tree / "rescore" / unit.parent.name)
    w.done(retrain_host, unit=f"rescore/{unit.parent.name}", complete_sha256=sha(unit),
           verified={"exit": 0, "tail": "names"},
           sc={"kind": "retrain", "fingerprints": {"complete_sha256": sha(unit), "checkpoints": {"e1": hx("e1"), "q": hx("q")},
                                                   "identity": {"manifest_sha256": None, "training_identity": None}}})
    w.fill(retrain=sha(unit))
    dry3 = w.init([{"kind": "a1_pass"}], amount=None, dry_run=True)
    assert [(p["kind"], p["engine"], p["cap_hours"]) for p in dry3["pods"]] == [("a1_pass", "Y", 16.5)]
    assert dry3["need_usd"] == cents(1.25 * cents(6 + 1.85 * 16.5)) == 45.66
    doc = w.pins78()                                     # R13: the anchor pin moved to another file after part 2
    doc["families"][w.family]["anchor_bank_sha256"] = sha(other)
    write(w.repo / w.rules.PINS_78B, doc)
    w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_78B, sha(w.repo / w.rules.PINS_78B))
    for script in ("representation_pass", "score_classifier", "score_l1_larf"):
        rel = f"{w.rules.SCORER_SETTINGS}/{script}__{w.family}.json"
        s = json.loads((w.repo / rel).read_text())
        if "anchor_bank_sha256" in s.get("pins", {}):
            s["pins"]["anchor_bank_sha256"] = sha(other)
            write(w.repo / rel, s)
            w.mp.setitem(w.rules.SCORER_PINS, rel, sha(w.repo / rel))
    index = json.loads((w.repo / w.rules.PINS_INDEX).read_text())
    index["pins_78b_sha256"] = sha(w.repo / w.rules.PINS_78B)
    write(w.repo / w.rules.PINS_INDEX, index)
    w.mp.setitem(w.rules.SCORER_PINS, w.rules.PINS_INDEX, sha(w.repo / w.rules.PINS_INDEX))
    with pytest.raises(SystemExit, match="the ANCHOR_BANK pin is not the anchor_file_sha256"):
        w.init([{"kind": "a1_pass"}], amount=None, dry_run=True)


BASE_UNIT = {"checkpoints": {"q": {"adapter_fingerprint": hx("q"), "optimizer_fingerprint": hx("q-opt")},
                             "e1": {"adapter_fingerprint": hx("e1"), "optimizer_fingerprint": hx("e1-opt")}},
             "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("man")}}


def unit_copy(doc):
    return json.loads(json.dumps(doc))


def test_k5_s3a_a_side_unit_without_an_e1_adapter_fingerprint_is_a_crash(so, monkeypatch, tmp_path):
    """S3a (K4bcr-R21): the acceptance needs the side unit's e1 adapter fingerprint."""
    side = unit_copy(BASE_UNIT)
    del side["checkpoints"]["e1"]["adapter_fingerprint"]
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", 0, side,
                                        {"complete": True, **unit_copy(BASE_UNIT)})
    assert rec["status"] == "crashed" and "no e1 adapter fingerprint" in rec["why"]


def test_k5_s3b_a_fingerprint_the_side_lists_and_the_regenerated_unit_omits_is_ls04(so, monkeypatch, tmp_path):
    """S3b (K4bcr-R7): a fingerprint the side unit lists and the regenerated unit omits is not equal (LS-04)."""
    regen = {"complete": True, **unit_copy(BASE_UNIT)}
    del regen["checkpoints"]["q"]["optimizer_fingerprint"]
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", 0, unit_copy(BASE_UNIT), regen)
    assert rec["status"] == "complete" and rec["acceptance"] is False and rec["reason"] == "LS-04"


def test_k5_s3c_an_identity_field_missing_on_both_sides_is_not_equal(so, monkeypatch, tmp_path):
    """S3c (K4bcr-R6): an identity field missing on both sides is not equal (LS-04)."""
    side, regen = unit_copy(BASE_UNIT), {"complete": True, **unit_copy(BASE_UNIT)}
    del side["identity"]["training_identity"], regen["identity"]["training_identity"]
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", 0, side, regen)
    assert rec["status"] == "complete" and rec["acceptance"] is False and rec["reason"] == "LS-04"


def test_k5_s4_record_done_refuses_acceptance_false_with_a_reason_other_than_ls04(so, monkeypatch):
    """S4 (K4bcr-R9): record-done refuses acceptance false with any reason but LS-04."""
    w = so
    w.fill(oext=True)
    side = w.side_unit(1101)
    w.pack(*oext_inputs(w), ("side_complete:a0:1101", side, sha(side)))
    host = w.init([REGEN])["released"][0]
    differs = {"kind": "COMPLETE (synthetic)", "complete": True,
               "checkpoints": {"e1": {"adapter_fingerprint": hx("e1"), "optimizer_fingerprint": hx("e1-opt")},
                               "q": {"adapter_fingerprint": hx("another q"), "optimizer_fingerprint": hx("q-opt")}},
               "identity": {"training_identity": hx("ti"), "manifest_sha256": hx("man")}}
    pod = ScPod(w, monkeypatch, host, unit_complete=differs)
    assert pod.main() == 0
    rec = pod.done()["jobs"][0]
    tree = w.root / "retrieved" / host / "tree"
    shutil.copytree(pod.root, tree)
    with pytest.raises(SystemExit, match="names no acceptance verdict"):
        w.done(host, unit=rec["unit"], complete_sha256=rec["complete_sha256"], verified={"exit": 0, "tail": ""},
               sc={"kind": "o_only_with_regenerate", "fingerprints": rec["sc"]["fingerprints"], "acceptance": False,
                   "acceptance_record_sha256": rec["sc"]["acceptance_record_sha256"]}, reason="LS-05")


@pytest.mark.parametrize("kind", ["retrain", "a1_pass", "o_only_with_regenerate"])
def test_k5_s5_a_unit_kinds_outputs_lie_under_its_job_folder_only(so, monkeypatch, tmp_path, kind):
    """S5 (K4bcr-R1, D1/PP18): a unit kind's recorded outputs are its job folder's files, never its unit's."""
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, kind)
    assert rec["status"] == "complete", rec.get("why")
    assert all(k.startswith("job-0/") for k in rec["outputs"]), sorted(rec["outputs"])


def test_k5_s6_the_backup_checks_a1_pass_and_the_retrains_recorded_outputs(so):
    """S6 (K4bcr-R17, D8): the backup checks a1_pass's recorded outputs (its cost ledger) too."""
    w = so
    backup = load_by_path("backup_sc_k5", w.root / "backup_records_stage1.py")
    tree = w.root / "retrieved" / "h" / "tree"
    attr = write(tree / "rescore" / "1101-attributes-a1" / "attributes.json", {"kind": "attributes (synthetic)"})
    unit = write(tree / "rescore" / "1101-attributes-a1" / "COMPLETE.json", {"files": {"attributes.json": sha(attr)}})
    ledger = write(tree / "job-0" / "cost-ledger.json", {"kind": "stage1 cost ledger"})
    plan = {"hosts": {"h": {"block": "sc", "jobs": [
        {"kind": "a1_pass", "status": "complete", "unit": "rescore/1101-attributes-a1", "complete_sha256": sha(unit),
         "outputs": {"job-0/cost-ledger.json": sha(ledger)}}]}}}
    staged = {f"units/h/{p.relative_to(tree)}": sha(p) for p in tree.rglob("*") if p.is_file()}
    missing = []
    backup.sealed_units(plan, ["h"], staged, missing)
    assert missing == []
    missing = []
    backup.sealed_units(plan, ["h"], {k: v for k, v in staged.items() if "cost-ledger" not in k}, missing)
    assert missing == ["h: job 0: 1 recorded output(s) not staged or changed"]


# ===== 9. round 5 (K5): the security re-verifier's R4 (the pack's scan over everything it ships) ====================
def test_k5_r4_the_pack_refuses_a_token_shaped_string_in_every_file_kind_it_ships(so, monkeypatch, request):
    """R4: a token-shaped string (built here, at test time; not a token) planted in an engine file, a scorer script,
    a setup-tar member, a generated payload (probe.json, through a monkeypatched probe_record) or the worker bootstrap
    (through a monkeypatched PIP_PIN) refuses the pack with names and pattern names only, never the text; no
    setup-receipt.json is written (release reads only a receipt). The edit files (edits/) are scanned; under data/
    only the files the prepared set's manifest does not pin are (K6, the lead's ruling on K5v-3; test_k6_*). Every file
    that holds the string is removed or restored when the test ends, pass or fail (K6, K5v-2)."""
    import re
    w = so
    fake = "hf_" + "K5" * 17                              # 'hf_' + 34 characters: the HF token's shape, not a token
    w.pack()                                             # a clean pack first (and the synthetic engine tree)
    out = w.root / "setup" / "packed-stage1-X"
    kept_bytes = {f: f.read_bytes() for f in (w.repo / w.rules.WRAPPER, w.root / "setup" / "extend_cap.py")}
    tmp = w.repo / "tmp" / "k5-r4"
    planted_files = [w.repo / "experiments" / "safety_selection" / "planted_k5.py", tmp / "edit.json", tmp / "rows.jsonl"]

    def cleanup():
        for f in planted_files:
            f.unlink(missing_ok=True)
        for f, data in kept_bytes.items():
            f.write_bytes(data)
    request.addfinalizer(cleanup)
    assert (out / "setup-receipt.json").is_file()
    pack = importlib.import_module("pack_setup")

    def refused(match: str, before_write: bool):
        with pytest.raises(SystemExit) as info:
            w.pack()
        text = str(info.value)
        assert re.search(match, text), text
        assert fake not in text and "K5K5" not in text
        assert not (out / "setup-receipt.json").exists()
        assert out.exists() is not before_write          # the bundle's own scan refuses before anything is written
        return text

    # an engine file (experiments/), then a scorer script (scripts/, at a test-local pin)
    planted = write(w.repo / "experiments" / "safety_selection" / "planted_k5.py", f"# {fake}\n")
    refused(r"a secret pattern is in a packed file: \[\('planted_k5.py', 'hf_token'\)\]", True)
    planted.unlink()
    script = w.repo / w.rules.WRAPPER
    original = script.read_bytes()
    script.write_bytes(original + f"# {fake}\n".encode())
    monkeypatch.setitem(w.rules.SCORER_PINS, w.rules.WRAPPER, sha(script))
    refused(r"a secret pattern is in a packed file: \[\('scorers_78b.py', 'hf_token'\)\]", True)
    script.write_bytes(original)
    monkeypatch.setitem(w.rules.SCORER_PINS, w.rules.WRAPPER, sha(script))
    # a generated payload (probe.json)
    real_probe = pack.probe_record
    monkeypatch.setattr(pack, "probe_record", lambda family: {**real_probe(family), "note": fake})
    refused(r"a secret pattern is in a packed file: \[\('probe.json', 'hf_token'\)\]", True)   # the payload scan
    monkeypatch.setattr(pack, "probe_record", real_probe)
    # the worker bootstrap (after the bundle is written: a partial folder, no receipt)
    monkeypatch.setattr(pack.rules, "PIP_PIN", fake)
    refused(r"^a secret pattern is in the generated bootstrap$", False)
    monkeypatch.setattr(pack.rules, "PIP_PIN", None)
    # a setup-tar member (setup/extend_cap.py of the working copy)
    member = w.root / "setup" / "extend_cap.py"
    kept = member.read_bytes()
    member.write_bytes(kept + f"# {fake}\n".encode())
    refused(r"a secret pattern is in a packed file: \[\('extend_cap.py', 'hf_token'\)\]", False)
    member.write_bytes(kept)
    w.pack()
    assert (out / "setup-receipt.json").is_file()        # clean again: the pack goes through
    # edits/ is scanned (K5); a data/ file stays outside the scan unless it is named in scan_anyway (K6: the prepared
    # set's files its manifest does not pin); inputs/ by its own loop
    edit = write(tmp / "edit.json", {"items": [{"prompt": fake}]})
    prepared = write(tmp / "rows.jsonl", json.dumps({"prompt": fake}) + "\n")
    with pytest.raises(SystemExit, match=r"a secret pattern is in a packed file: \[\('edit.json', 'hf_token'\)\]"):
        pack.refuse_secrets({f"edits/{hx('e')}.edit.json": edit}, {}, pack.DATA_PREFIXES)
    pack.refuse_secrets({"data/kt-prepared/x/rows.jsonl": prepared}, {}, pack.DATA_PREFIXES)
    with pytest.raises(SystemExit, match=r"a secret pattern is in a packed file: \[\('rows.jsonl', 'hf_token'\)\]"):
        pack.refuse_secrets({"data/kt-prepared/x/rows.jsonl": prepared}, {}, pack.DATA_PREFIXES,
                            frozenset({"data/kt-prepared/x/rows.jsonl"}))
    assert pack.DATA_PREFIXES == ("data/", "inputs/")


# ===== 10. round 6 (K6): the K5 re-verifier's V1, V2 and K5v-6; the lead's rulings on K5v-3 and item 23 ==============
# V1 (K5v-D1c): c0 refuses a packed source unit that is a symbolic link, even when its target has the pinned bytes
def test_k6_v1_c0_refuses_a_linked_source_unit_even_when_its_target_has_the_pinned_bytes(so, tmp_path):
    runner = load_by_path("jr78_k6_v1", so.root / "setup" / "job_runner_stage1.py")
    good = {"kind": "COMPLETE (synthetic)", "checkpoints": {"e1": {"adapter_fingerprint": hx("the real e1")}}}
    rel = "inputs/source_complete-R-1101/COMPLETE.json"
    target = write(tmp_path / "elsewhere" / "COMPLETE.json", good)
    (tmp_path / rel).parent.mkdir(parents=True)
    (tmp_path / rel).symlink_to(target)
    pins = {"source_complete:R:1101": sha(target), "oext_bank": hx("ob"), "oext_record": hx("or")}
    inputs = {"source_complete:R:1101": rel, "oext_bank": "inputs/oext_bank/b.json",
              "oext_record": "inputs/oext_record/r.json"}
    doc = {"files": {inputs[n]: pins[n] for n in pins}, "inputs": inputs}
    job = {"kind": "c0", "arm": "R", "seed": 1101, "recipe": "B", "engine": "X", "inputs": pins,
           "edit": {"sha256": hx("rd1"), "path": "x"}, "expect_fingerprint": hx("the real e1")}
    with pytest.raises(runner.Unrunnable, match="is missing or differs from its pin"):
        runner.job_commands(sc_plan(so, job), "h", 0, tmp_path, {}, doc)


# V2 (the K5v-R21 variant): a side unit with no e1 checkpoint at all is a crash (S3a deletes only the fingerprint)
def test_k6_v2_a_side_unit_with_no_e1_checkpoint_is_a_crash(so, monkeypatch, tmp_path):
    side = unit_copy(BASE_UNIT)
    del side["checkpoints"]["e1"]
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", 0, side,
                                        {"complete": True, **unit_copy(BASE_UNIT)})
    assert rec["status"] == "crashed" and "no e1 adapter fingerprint" in rec["why"]


def k6_prepared(w, listed: dict, extra: dict) -> tuple[Path, str]:
    """The synthetic prepared set rewritten for K6: ``listed`` files (relative path -> text) named in manifest.json's
    "files" map at their SHA-256, ``extra`` files (relative path -> text) not named; returns (folder, SHA-256 of the
    new manifest.json). manifest.sha256 keeps the family's pin (so manifest.json is NOT at the pin, as in every
    synthetic world; the tests that need it at the pin pass this SHA-256 to prepared_files)."""
    folder = w.repo / w.rules.PREPARED_LOCAL / w.rules.PREPARED_NAME
    names = {}
    for rel, text in listed.items():
        names[rel] = sha(write(folder / rel, text))
    for rel, text in extra.items():
        write(folder / rel, text)
    man = write(folder / "manifest.json", {"kind": "prepared (synthetic, K6)", "files": names})
    return folder, sha(man)


def test_k6_prepared_files_scans_what_the_manifest_does_not_pin_and_skips_macos_metadata_by_name(so):
    """K5v-3 (the lead's ruling): a file manifest.json lists at its listed SHA-256 stays outside the scan; a listed
    file whose bytes changed, every unlisted file (prepare_receipt.json, manifest.json and manifest.sha256, a stray
    file) is packed and scanned; .DS_Store, AppleDouble '._*' files and the volume metadata folders are skipped by
    name (neither packed nor scanned); the manifest's list counts only while manifest.json is at the pin given."""
    w = so
    w.pack()                                             # the synthetic prepared folder (manifest.sha256, manifest.json)
    pack = importlib.import_module("pack_setup")
    folder, digest = k6_prepared(w, {"engine/train_rows.jsonl": "{}\n", "banks/dev.jsonl": "{}\n"},
                                 {"prepare_receipt.json": "{}\n", "stray.txt": "x\n", ".DS_Store": "finder\n",
                                  "engine/._train_rows.jsonl": "appledouble\n", ".Spotlight-V100/store.db": "s\n"})
    write(folder / "banks" / "dev.jsonl", "{} changed after the manifest\n")
    packed, scan, skipped = pack.prepared_files(folder, digest)
    assert sorted(scan) == ["banks/dev.jsonl", "manifest.json", "manifest.sha256", "prepare_receipt.json", "stray.txt"]
    assert sorted(packed) == sorted(scan | {"engine/train_rows.jsonl"})
    assert sorted(skipped) == [".DS_Store", ".Spotlight-V100/store.db", "engine/._train_rows.jsonl"]
    assert all(packed[rel] == (folder / rel, sha(folder / rel)) for rel in packed)
    _, scan2, skipped2 = pack.prepared_files(folder, hx("not the manifest's SHA-256"))   # off the pin: no file listed
    assert sorted(scan2) == sorted(scan | {"engine/train_rows.jsonl"}) and sorted(skipped2) == sorted(skipped)
    write(folder / "manifest.json", {"kind": "prepared (synthetic, K6)", "files": ["engine/train_rows.jsonl"]})
    assert "engine/train_rows.jsonl" in pack.prepared_files(folder, sha(folder / "manifest.json"))[1]   # no map
    assert [pack.macos_metadata(n) for n in (".DS_Store", "a/.DS_Store", "._x", "Icon\r", ".Trashes/1", "x.DS_Store",
                                             "prepare_receipt.json", "a._b", ".notes", "a/.env")] == [True] * 5 + [False] * 5


def test_k6_the_pack_refuses_a_token_shaped_string_in_an_unlisted_data_file_and_ships_no_macos_metadata(so, request):
    """K5v-3 through the real pack: a token-shaped string (built here, not a token) in prepare_receipt.json or in a
    stray file of the prepared set refuses the pack with names and pattern names only, before anything is written; the
    same string in .DS_Store or an AppleDouble file does not refuse, and neither file is in the bundle. Every planted
    file is removed when the test ends (K5v-2)."""
    import tarfile
    w = so
    fake = "hf_" + "K6" * 17                              # 'hf_' + 34 characters: the HF token's shape, not a token
    w.pack()
    folder = w.repo / w.rules.PREPARED_LOCAL / w.rules.PREPARED_NAME
    planted = [folder / "prepare_receipt.json", folder / "stray" / "notes.txt", folder / ".DS_Store",
               folder / "._manifest.json"]
    request.addfinalizer(lambda: [p.unlink(missing_ok=True) for p in planted])
    out = w.root / "setup" / "packed-stage1-X"
    for p in planted[:2]:
        write(p, {"note": fake})
        with pytest.raises(SystemExit) as info:
            w.pack()
        text = str(info.value)
        assert text == f"a secret pattern is in a packed file: [({p.name!r}, 'hf_token')]", text
        assert fake not in text and not out.exists()
        p.unlink()
    for p in planted[2:]:
        write(p, {"note": fake})
    w.pack()
    with tarfile.open(out / "bundle-stage1-X.tar.gz") as tf:
        names = [m.name for m in tf if m.isfile()]
        data = [n for n in names if n.startswith("data/")]
        assert not [n for n in names if n.rsplit("/", 1)[-1] in (".DS_Store", "._manifest.json")]
        assert not [n for n in names if fake.encode() in tf.extractfile(n).read()]
    assert f"data/kt-prepared/{w.rules.PREPARED_NAME}/manifest.json" in data
    sealed = json.loads((out / "sealed-files.json").read_text())
    assert not [n for n in sealed["files"] if n.endswith((".DS_Store", "._manifest.json"))]


def test_k6_k5v6_the_bundle_scan_at_its_call_site_gets_the_edits_and_the_unpinned_data_files(so, monkeypatch):
    """K5v-6: a spy on refuse_secrets (and on secret_scan.scan_paths) in a real pack. The bundle's call skips exactly
    DATA_PREFIXES (data/ and inputs/), and the files it scans include the three R_d edit files under edits/ and the
    prepared set's unpinned files (prepare_receipt.json, manifest.json, manifest.sha256) but not a manifest-listed one
    (manifest.json at the pin here: prepared_files is given its SHA-256). The setup tar's call skips nothing."""
    w = so
    w.pack()
    pack = importlib.import_module("pack_setup")
    folder, digest = k6_prepared(w, {"engine/train_rows.jsonl": "{}\n"}, {"prepare_receipt.json": "{}\n"})
    real_prepared, real_refuse, real_scan = pack.prepared_files, pack.refuse_secrets, pack.secret_scan.scan_paths
    monkeypatch.setattr(pack, "prepared_files", lambda f, d: real_prepared(f, digest if f == folder else d))
    calls, scanned = [], []

    def refuse_spy(files, payloads, prefixes, scan_anyway=frozenset()):
        calls.append({"files": dict(files), "payloads": sorted(payloads), "prefixes": prefixes,
                      "scan_anyway": set(scan_anyway)})
        return real_refuse(files, payloads, prefixes, scan_anyway)
    monkeypatch.setattr(pack, "refuse_secrets", refuse_spy)
    monkeypatch.setattr(pack.secret_scan, "scan_paths", lambda paths: (scanned.extend(str(p) for p in paths),
                                                                       real_scan(paths))[1])
    w.pack()
    assert len(calls) == 2
    bundle, setup = calls
    assert "bundle-manifest.json" in bundle["payloads"] and bundle["prefixes"] == ("data/", "inputs/")
    assert setup["prefixes"] == () and setup["scan_anyway"] == set()
    edits = {n: f for n, f in bundle["files"].items() if n.startswith("edits/")}
    assert len(edits) == 3 and all(str(f) in scanned for f in edits.values())
    base = f"data/kt-prepared/{w.rules.PREPARED_NAME}/"
    assert bundle["scan_anyway"] == {base + n for n in ("manifest.json", "manifest.sha256", "prepare_receipt.json")}
    assert all(str(bundle["files"][n]) in scanned for n in bundle["scan_anyway"])
    listed = bundle["files"][base + "engine/train_rows.jsonl"]
    assert listed == folder / "engine" / "train_rows.jsonl" and str(listed) not in scanned


# Item 23 (the 7 Nov ruling): the Mac-side check that the packed c0 source unit's e1 fingerprint is C0_SOURCE's
@pytest.mark.parametrize("case", ["typo", "q-not-e1", "no-e1", "unreadable"])
def test_k6_item23_the_pack_refuses_a_c0_source_whose_e1_fingerprint_is_not_c0_sources(so, case):
    """The pack (and its dry run) reads the packed source unit's checkpoints.e1.adapter_fingerprint (the file at
    C0_SOURCE's complete_sha256) and refuses, names only, when it is not C0_SOURCE's e1_fingerprint (a typing error in
    the lead's step), when only another checkpoint holds that value, when e1 lists none, or when the file is not JSON;
    nothing is packed, so no pod can start. The right value packs (test_c0_and_o_only_with_test_local_oext_and_c0_pins)."""
    w = so
    w.fill(oext=True, c0=True)
    src = w.c0_source()
    expect = hx("e1-R-1101")
    if case == "typo":
        expect = hx("a typo in the step")
    elif case == "q-not-e1":
        write(src, {"kind": "COMPLETE (synthetic)", "checkpoints": {"q": {"adapter_fingerprint": expect},
                                                                    "e1": {"adapter_fingerprint": hx("another e1")}}})
    elif case == "no-e1":
        write(src, {"kind": "COMPLETE (synthetic)", "checkpoints": {"q": {"adapter_fingerprint": expect}}})
    else:
        write(src, "not json {\n")
    w.mp.setitem(w.r78.C0_SOURCE, w.family, {"complete_sha256": sha(src), "e1_fingerprint": expect})
    want = {"typo": "its e1 adapter fingerprint is not C0_SOURCE's e1_fingerprint", "q-not-e1": "is not C0_SOURCE's",
            "no-e1": "lists no e1 adapter fingerprint", "unreadable": "is not a readable COMPLETE.json"}[case]
    for dry in (True, False):
        with pytest.raises(SystemExit) as info:
            w.pack(*oext_inputs(w), ("source_complete:R:1101", src, sha(src)), dry_run=dry)
        text = str(info.value)
        assert text.startswith("--inputs FILE: 'source_complete:R:1101' (c0's source unit)") and want in text, text
        assert expect not in text and hx("another e1") not in text
        assert expect[:12] not in text and hx("another e1")[:12] not in text   # K6v-6: no fingerprint prefix either
    assert not (w.root / "setup" / "packed-stage1-X").exists()


def test_k6v1_an_unlisted_prepared_file_with_a_binary_suffix_is_packed_and_scanned(so, request):
    """K6v-1 (K6V's T1; the K5v-3 ruling): an unlisted file of the prepared set with a binary suffix (.npy, .gz,
    .safetensors, ...) is packed AND scanned like any unlisted file; a token-shaped string (built here, not a token) in
    it refuses the real pack, names only, before anything is written. Every planted file is removed afterwards."""
    w = so
    w.pack()
    pack = importlib.import_module("pack_setup")
    folder, digest = k6_prepared(w, {"engine/train_rows.jsonl": "{}\n"}, {})
    names = ["extra/blob.npy", "extra/archive.gz", "extra/w.safetensors", "extra/x.bin"]
    for n in names:
        write(folder / n, "binary stand-in\n")
    request.addfinalizer(lambda: [(folder / n).unlink(missing_ok=True) for n in names])
    packed, scan, _ = pack.prepared_files(folder, digest)
    assert set(names) <= set(scan) and set(names) <= set(packed)
    assert "engine/train_rows.jsonl" in packed and "engine/train_rows.jsonl" not in scan
    fake = "hf_" + "K6" * 17                              # the HF token's shape, not a token
    real = w.repo / w.rules.PREPARED_LOCAL / w.rules.PREPARED_NAME / "stray" / "blob.npy"
    request.addfinalizer(lambda: real.unlink(missing_ok=True))
    write(real, {"note": fake})
    out = w.root / "setup" / "packed-stage1-X"
    with pytest.raises(SystemExit) as info:
        w.pack()
    assert str(info.value) == "a secret pattern is in a packed file: [('blob.npy', 'hf_token')]", str(info.value)
    assert fake not in str(info.value) and not out.exists()


# ===== R2 K2: the planning tests reach the scorer mutation runner ===================================================
# run_mutants_scorer_78b.py runs this file alone (its TEST); the planning layer's mutants (plan_tool.py, rules_78b.py,
# judge_units_stage1.py, seal.py, states_tool.py) are in this file's spec, so when this file is named alone on the
# command line its module also holds tests/test_planning_ab_78b.py's tests and fixtures (by name; nothing else of that
# module is imported, so no helper here is shadowed). The full suite names the folder, and each test runs once there.
if any(a.endswith("test_scorer_block_78b.py") for a in sys.argv) and \
        not any(a.rstrip("/").endswith(("test_planning_ab_78b.py", "tests")) for a in sys.argv):
    import test_planning_ab_78b as _planning_ab
    for _name in dir(_planning_ab):
        if _name.startswith("test_") or _name in ("wa", "waf", "wb"):
            assert _name not in globals(), _name
            globals()[_name] = getattr(_planning_ab, _name)
