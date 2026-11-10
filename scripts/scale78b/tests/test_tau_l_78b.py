"""tau_l_78b.py on synthetic unit folders only (R1 Track C; Part 2 section 4.7; DES K2; GXB O9). Each fixture unit holds
COMPLETE.json in the engine's form (``experiments/safety_selection/ledger.py`` write_complete, ``runner.py`` :492-509),
eval/e1/query_loss.jsonl, and decoy files (summary, guard labels, answers) that hold a planted sentinel: the tests prove
that only COMPLETE.json and query_loss.jsonl are opened and that no loss per unit, no label and no text is printed or
written. No real unit is opened."""

from __future__ import annotations

import builtins
import importlib.util
import json
import math
import statistics
from pathlib import Path

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.scale78b import tau_l_78b as tl

ROOT = Path(__file__).resolve().parents[3]
SENT = "QZXJ-planted-sentinel-label-9031"
# REQ-19's sealed 1B known answer (R: research/experiments/2026-10-16-stage1-commitments.md:221; PR4:593, :595).
KNOWN_MEANS = {1101: 1.5424909447459505, 1102: 1.5472398312762379, 1103: 1.5449415715783834}
KNOWN_S, KNOWN_TAU = 0.002374850619448416, 0.0067170919092681925


def make_unit(root: Path, family: str, seed: int, losses, *, edit=None, loss_lines=None, decoys=True) -> tuple[Path, str]:
    """A unit folder; returns (folder, COMPLETE.json SHA-256). edit(marker) may change COMPLETE.json before it is
    written; loss_lines replaces the query_loss.jsonl bytes."""
    folder = root / f"{family}-{seed}-a0-e1"
    (folder / "eval" / "e1").mkdir(parents=True)
    if loss_lines is None:
        loss_lines = b"".join(json.dumps({"query_id": f"q-{k:03d}", "input_tokens": 10, "target_tokens": 3,
                                          "token_sha256": "0" * 64, "loss": v}).encode() + b"\n"
                              for k, v in enumerate(losses))
    (folder / tl.LOSS_FILE).write_bytes(loss_lines)
    files = {tl.LOSS_FILE: sha256_bytes(loss_lines)}
    if decoys:
        for name, data in (("eval/e1/summary.json", json.dumps({"note": SENT}).encode()),
                           ("eval/e1/guard.jsonl", json.dumps({"kind": "overrefusal", "label": SENT}).encode() + b"\n"),
                           ("eval/e1/generations.jsonl", json.dumps({"answer": SENT}).encode() + b"\n")):
            (folder / name).write_bytes(data)
            files[name] = sha256_bytes(data)
    finite = [v for v in losses if isinstance(v, float) and math.isfinite(v)] if losses else []
    mean = math.fsum(finite) / len(finite) if finite else 0.0
    marker = {"complete": True, "completed_utc": "2026-11-01T00:00:00+00:00", "kind": "run-one",
              "identity": {"manifest_sha256": tl.MANIFESTS[family], "training_identity": tl.TRAINING_IDENTITY[family],
                           "recipe_sha256": "1" * 64, "code_sha256": "2" * 64, "data_config_sha256": "3" * 64},
              "job_sha256": "4" * 64,
              "trajectory": {"split": "ref", "arm": "a0", "seed": seed, "role": "calibration"},
              "target_checkpoint": "e1", "checkpoints": {"e1": {"step": 33}},
              "evaluation": {"checkpoint": "e1", "query_loss": {"n": len(finite), "mean": mean,
                                                                 "query_bank_sha256": "5" * 64},
                             "overrefusal": {"refusals": 7, "note": SENT}},
              "files": files}
    if edit is not None:
        edit(marker)
    data = json.dumps(marker, indent=1).encode()
    (folder / "COMPLETE.json").write_bytes(data)
    return folder, sha256_bytes(data)


def three_units(root: Path, family: str = "olmo2-7b", means=KNOWN_MEANS, edits=None, **kw):
    units, pins = {}, {}
    for seed in tl.SEEDS:
        losses = kw.pop(f"losses_{seed}", None) or [means[seed]] * 200
        folder, digest = make_unit(root, family, seed, losses, edit=(edits or {}).get(seed))
        units[seed], pins[seed] = folder, digest
    return units, pins


def argv_of(family, units, pins, out=None):
    argv = ["--family", family]
    for seed in tl.SEEDS:
        argv += ["--unit", f"{seed}={units[seed]}:{pins[seed]}"]
    if out is not None:
        argv += ["--out", str(out)]
    return argv


def run(argv, capsys, pins):
    code = tl.main(argv, unit_pins=pins)
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def test_known_answer_req19(tmp_path, capsys):
    """REQ-19's 1B means give REQ-19's sealed s and τ_L (the formula of Part 2 section 4.7 and PR4:589)."""
    units, pins = three_units(tmp_path)
    out = tmp_path / "rec.json"
    code, so, se = run(argv_of("olmo2-7b", units, pins, out), capsys, pins)
    assert code == 0, se
    doc = json.loads(out.read_bytes())
    assert math.isclose(doc["s"], KNOWN_S, rel_tol=1e-9) and math.isclose(doc["tau_l"], KNOWN_TAU, rel_tol=1e-9)
    assert doc["tau_l"] == 2 * math.sqrt(2) * doc["s"]
    assert (doc["n"], doc["ddof"], doc["rows"], doc["checkpoint"]) == (3, 1, 200, "e1")
    assert repr(doc["s"]) in so and repr(doc["tau_l"]) in so


def test_s_is_the_ddof_1_sd_of_the_unit_means(tmp_path, capsys):
    rng = [((k * 7919) % 200) / 1000.0 for k in range(200)]
    losses = {1101: [1.2 + x for x in rng], 1102: [1.25 + x * 0.9 for x in rng], 1103: [1.1 + x * 1.3 for x in rng]}
    units, pins = three_units(tmp_path, **{f"losses_{s}": v for s, v in losses.items()})
    code, so, se = run(argv_of("olmo2-7b", units, pins), capsys, pins)
    assert code == 0, se
    means = [math.fsum(losses[s]) / 200 for s in tl.SEEDS]
    s = statistics.stdev(means)
    assert repr(s) in so and repr(2 * math.sqrt(2) * s) in so
    assert statistics.pstdev(means) != s                         # ddof 1, not 0


def test_record_holds_only_s_n_tau_and_hashes(tmp_path, capsys):
    units, pins = three_units(tmp_path)
    out = tmp_path / "rec.json"
    code, so, se = run(argv_of("olmo2-7b", units, pins, out), capsys, pins)
    doc = json.loads(out.read_bytes())
    assert set(doc) == {"kind", "version", "family", "rule", "n", "ddof", "rows", "checkpoint", "s", "tau_l", "inputs",
                        "query_bank_sha256", "read", "provenance"}
    for seed in tl.SEEDS:
        entry = doc["inputs"][str(seed)]
        assert set(entry) == {"complete_sha256", "query_loss_sha256", "pin_source"}
        assert entry["complete_sha256"] == pins[seed]
        assert entry["query_loss_sha256"] == sha256_bytes((units[seed] / tl.LOSS_FILE).read_bytes())
    blob = out.read_text() + so + se
    for m in KNOWN_MEANS.values():                               # no loss per unit is printed or written
        assert repr(m) not in blob and f"{m:.6f}" not in blob
    assert SENT not in blob
    assert doc["query_bank_sha256"] == "5" * 64


def test_only_complete_and_query_loss_are_opened(tmp_path, capsys, monkeypatch):
    units, pins = three_units(tmp_path)
    opened = []
    real_read_bytes, real_open = Path.read_bytes, builtins.open

    def spy_read_bytes(self):
        opened.append(Path(self).resolve())
        return real_read_bytes(self)

    def spy_open(file, *a, **k):
        if isinstance(file, (str, Path)):
            opened.append(Path(file).resolve())
        return real_open(file, *a, **k)
    monkeypatch.setattr(Path, "read_bytes", spy_read_bytes)
    monkeypatch.setattr(builtins, "open", spy_open)
    code, so, se = run(argv_of("olmo2-7b", units, pins, tmp_path / "rec.json"), capsys, pins)
    monkeypatch.undo()
    assert code == 0, se
    inside = sorted({p for p in opened if any(u.resolve() in p.parents for u in units.values())})
    expected = sorted({(units[s] / name).resolve() for s in tl.SEEDS for name in ("COMPLETE.json", tl.LOSS_FILE)})
    assert inside == expected


@pytest.mark.parametrize("case,message", [
    ("not_complete", "not a complete marker"),
    ("no_files", "not a complete marker"),
    ("checkpoint_q", "target_checkpoint is not e1"),
    ("arm_r", "trajectory is not arm a0 at seed 1102"),
    ("seed_other", "trajectory is not arm a0 at seed 1102"),
    ("seed_bool", "trajectory is not arm a0"),
    ("training_identity", "training identity is not olmo2-7b's"),
    ("manifest", "prepared manifest is not olmo2-7b's"),
    ("eval_checkpoint", "evaluation is not checkpoint e1 over 200"),
    ("eval_n", "evaluation is not checkpoint e1 over 200"),
    ("mean_ulp", "recomputed mean query loss differs"),
    ("mean_bool", "recorded mean query loss is not a finite number"),
    ("no_bank", "names no query bank"),
    ("not_listed", "does not list eval/e1/query_loss.jsonl"),
    ("listed_other", "query_loss.jsonl hashes to"),
])
def test_complete_json_checks(tmp_path, capsys, case, message):
    def edit(m):
        if case == "not_complete":
            m["complete"] = False
        elif case == "no_files":
            del m["files"]
        elif case == "checkpoint_q":
            m["target_checkpoint"] = "q"
        elif case == "arm_r":
            m["trajectory"]["arm"] = "R"
        elif case == "seed_other":
            m["trajectory"]["seed"] = 1101
        elif case == "seed_bool":
            m["trajectory"]["seed"] = True
        elif case == "training_identity":
            m["identity"]["training_identity"] = "a" * 64
        elif case == "manifest":
            m["identity"]["manifest_sha256"] = tl.MANIFESTS["llama31-8b"]
        elif case == "eval_checkpoint":
            m["evaluation"]["checkpoint"] = "q"
        elif case == "eval_n":
            m["evaluation"]["query_loss"]["n"] = 199
        elif case == "mean_ulp":
            m["evaluation"]["query_loss"]["mean"] = math.nextafter(m["evaluation"]["query_loss"]["mean"], 2.0)
        elif case == "mean_bool":
            m["evaluation"]["query_loss"]["mean"] = True
        elif case == "no_bank":
            m["evaluation"]["query_loss"]["query_bank_sha256"] = None
        elif case == "not_listed":
            del m["files"][tl.LOSS_FILE]
        elif case == "listed_other":
            m["files"][tl.LOSS_FILE] = "6" * 64
    units, pins = three_units(tmp_path, edits={1102: edit})
    out = tmp_path / "rec.json"
    code, so, se = run(argv_of("olmo2-7b", units, pins, out), capsys, pins)
    assert code == 2 and message in se and not out.exists() and so == ""
    assert SENT not in se


@pytest.mark.parametrize("case,message", [
    ("rows_199", "holds 199 rows, not 200"),
    ("repeated_id", "no query id or a repeated one"),
    ("nan", "is not strict JSON"),
    ("bool_loss", "loss is not a finite number"),
    ("string_loss", "loss is not a finite number"),
    ("blank_line", "is not strict JSON"),
    ("no_id", "no query id or a repeated one"),
])
def test_query_loss_checks(tmp_path, capsys, case, message):
    lines = [{"query_id": f"q-{k:03d}", "loss": 1.5} for k in range(200)]
    if case == "rows_199":
        lines = lines[:199]
    elif case == "repeated_id":
        lines[5]["query_id"] = "q-004"
    elif case == "bool_loss":
        lines[9]["loss"] = True
    elif case == "string_loss":
        lines[9]["loss"] = "1.5"
    elif case == "no_id":
        del lines[3]["query_id"]
    data = b"".join(json.dumps(x).encode() + b"\n" for x in lines)
    if case == "nan":
        data = data.replace(b'"loss": 1.5}', b'"loss": NaN}', 1)
    elif case == "blank_line":
        data = data.replace(b"\n", b"\n\n", 1)
    units, pins = three_units(tmp_path)
    folder, digest = make_unit(tmp_path / "x", "olmo2-7b", 1103, [1.5] * 200, loss_lines=data,
                               edit=lambda m: m["evaluation"]["query_loss"].update(n=200, mean=1.5))
    units[1103], pins[1103] = folder, digest
    code, so, se = run(argv_of("olmo2-7b", units, pins), capsys, pins)
    assert code == 2 and message in se, se


def test_units_must_share_the_query_bank(tmp_path, capsys):
    units, pins = three_units(tmp_path, edits={1103: lambda m: m["evaluation"]["query_loss"].update(
        query_bank_sha256="7" * 64)})
    code, so, se = run(argv_of("olmo2-7b", units, pins), capsys, pins)
    assert code == 2 and "same query bank" in se


def test_units_must_hold_the_same_rows(tmp_path, capsys):
    units, pins = three_units(tmp_path)
    lines = b"".join(json.dumps({"query_id": f"x-{k:03d}", "loss": KNOWN_MEANS[1102]}).encode() + b"\n"
                     for k in range(200))
    folder, digest = make_unit(tmp_path / "x", "olmo2-7b", 1102, [KNOWN_MEANS[1102]] * 200, loss_lines=lines)
    units[1102], pins[1102] = folder, digest
    code, so, se = run(argv_of("olmo2-7b", units, pins), capsys, pins)
    assert code == 2 and "same task rows" in se


def test_error_txt_refuses(tmp_path, capsys):
    units, pins = three_units(tmp_path)
    (units[1101] / "error.txt").write_text(SENT)
    code, so, se = run(argv_of("olmo2-7b", units, pins), capsys, pins)
    assert code == 2 and "error.txt" in se and SENT not in se


def test_complete_json_bytes_must_hash_to_the_pin(tmp_path, capsys):
    units, pins = three_units(tmp_path)
    marker = units[1102] / "COMPLETE.json"
    marker.write_bytes(marker.read_bytes() + b"\n")
    code, so, se = run(argv_of("olmo2-7b", units, pins), capsys, pins)
    assert code == 2 and "COMPLETE.json hashes to" in se


def test_two_seeds_one_folder_refused(tmp_path, capsys):
    units, pins = three_units(tmp_path)
    pins_same = {**pins, 1102: pins[1101]}
    units_same = {**units, 1102: units[1101]}
    code, so, se = run(argv_of("olmo2-7b", units_same, pins_same), capsys, pins_same)
    assert code == 2 and "trajectory is not arm a0 at seed 1102" in se      # the seed check sees it first


def test_literal_pins_refuse_fixture_units(tmp_path, capsys):
    """The real literal pins (no fixture hook): a fixture unit is not OLMo-2-7B's registered a0-1101."""
    units, pins = three_units(tmp_path)
    code = tl.main(argv_of("olmo2-7b", units, pins))
    cap = capsys.readouterr()
    assert code == 2 and f"olmo2-7b's a0-1101 is {tl.UNIT_PINS['olmo2-7b'][1101]}" in cap.err


def test_llama_1103_takes_its_pin_from_the_command_line(tmp_path, capsys):
    """Llama's N a0-1103 has no literal pin: the command line's pin is used and the record says so."""
    units, pins = three_units(tmp_path, family="llama31-8b")
    hook = {1101: pins[1101], 1102: pins[1102], 1103: None}
    out = tmp_path / "rec.json"
    code, so, se = run(argv_of("llama31-8b", units, pins, out), capsys, hook)
    assert code == 0, se
    doc = json.loads(out.read_bytes())
    assert doc["inputs"]["1103"]["pin_source"].startswith("command line")
    assert doc["inputs"]["1101"]["pin_source"] == "literal"
    assert doc["inputs"]["1103"]["complete_sha256"] == pins[1103]
    assert tl.UNIT_PINS["llama31-8b"][1103] is None


def test_llama_unit_needs_llamas_identity(tmp_path, capsys):
    units, pins = three_units(tmp_path, family="olmo2-7b")
    code, so, se = run(argv_of("llama31-8b", units, pins), capsys, pins)
    assert code == 2 and "training identity is not llama31-8b's" in se


@pytest.mark.parametrize("argv_edit,message", [
    (lambda a: a[:-2], "needs seed 1103"),
    (lambda a: a + a[-2:], "names seed 1103 twice"),
    (lambda a: a[:-1] + [a[-1].replace("1103=", "1104=")], "seed 1104 is not one of"),
    (lambda a: a[:-1] + [a[-1].rsplit(":", 1)[0] + ":XYZ"], "SEED=FOLDER:SHA256"),
    (lambda a: a[:-1] + [a[-1].replace("1103=", "")], "SEED=FOLDER:SHA256"),
])
def test_unit_options(tmp_path, capsys, argv_edit, message):
    units, pins = three_units(tmp_path)
    code, so, se = run(argv_edit(argv_of("olmo2-7b", units, pins)), capsys, pins)
    assert code == 2 and message in se, se


def test_out_created_once_and_never_inside_a_unit(tmp_path, capsys):
    units, pins = three_units(tmp_path)
    out = tmp_path / "rec.json"
    out.write_text("x")
    code, so, se = run(argv_of("olmo2-7b", units, pins, out), capsys, pins)
    assert code == 2 and "exists" in se and out.read_text() == "x"
    inside = units[1102] / "eval" / "rec.json"
    code, so, se = run(argv_of("olmo2-7b", units, pins, inside), capsys, pins)
    assert code == 2 and "inside a unit" in se and not inside.exists()
    nowhere = tmp_path / "missing" / "rec.json"
    code, so, se = run(argv_of("olmo2-7b", units, pins, nowhere), capsys, pins)
    assert code == 2 and "folder does not exist" in se


def test_without_out_nothing_is_written(tmp_path, capsys):
    units, pins = three_units(tmp_path)
    before = sorted(p for p in tmp_path.rglob("*"))
    code, so, se = run(argv_of("olmo2-7b", units, pins), capsys, pins)
    assert code == 0 and "wrote" not in so
    assert sorted(p for p in tmp_path.rglob("*")) == before


def test_pins_equal_rk():
    """UNIT_PINS, TRAINING_IDENTITY and MANIFESTS equal the 7-8B kit's KIT and MANIFESTS (runkit/stage1-78b/rules_78b.py,
    standard library only, loaded by path)."""
    spec = importlib.util.spec_from_file_location("rk_for_tau_l_test", ROOT / "runkit/stage1-78b/rules_78b.py")
    rk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rk)
    for family in tl.FAMILIES:
        side = {s: u["complete_sha256"] for s, u in rk.KIT[family]["a0_units"].items() if s != "untuned"}
        literal = {s: p for s, p in tl.UNIT_PINS[family].items() if p is not None}
        assert literal == side
        assert tl.TRAINING_IDENTITY[family] == rk.KIT[family]["training_identity"]
        assert tl.MANIFESTS[family] == rk.MANIFESTS[family]
    assert set(tl.UNIT_PINS["llama31-8b"]) - set(rk.KIT["llama31-8b"]["a0_units"]) == {1103}


# ----- the fix round (verifier C1, C5, C9) -------------------------------------------------------------------------


def test_a_failed_write_leaves_no_file(tmp_path, capsys, monkeypatch):
    """C1: ENOSPC after half the bytes leaves neither --out nor a partial file."""
    import errno

    units, pins = three_units(tmp_path)
    folder = tmp_path / "out"
    folder.mkdir()
    out = folder / "rec.json"
    real_open = builtins.open

    class Half:
        def __init__(self, handle):
            self.handle = handle

        def write(self, data):
            self.handle.write(data[: len(data) // 2])
            self.handle.flush()
            raise OSError(errno.ENOSPC, "No space left on device")

        def __getattr__(self, name):
            return getattr(self.handle, name)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.handle.close()
            return False

    def failing_open(file, mode="r", *a, **k):
        handle = real_open(file, mode, *a, **k)
        return Half(handle) if "x" in mode and Path(file).resolve().parent == folder.resolve() else handle
    monkeypatch.setattr(builtins, "open", failing_open)
    code, so, se = run(argv_of("olmo2-7b", units, pins, out), capsys, pins)
    monkeypatch.undo()
    assert code == 2 and "cannot be written (OSError)" in se and so == ""
    assert not out.exists() and list(folder.iterdir()) == []


def test_write_once_leaves_only_the_complete_record(tmp_path):
    out = tmp_path / "rec.json"
    tl.write_once(out, b"abc")
    assert out.read_bytes() == b"abc" and [p.name for p in tmp_path.iterdir()] == ["rec.json"]
    with pytest.raises(tl.Refusal, match="created once"):
        tl.write_once(out, b"xyz")
    assert out.read_bytes() == b"abc" and [p.name for p in tmp_path.iterdir()] == ["rec.json"]


def test_a_systemexit_with_text_is_caught(tmp_path, capsys, monkeypatch):
    """C5: a SystemExit carrying text inside main is reported by its class only, exit 2."""
    units, pins = three_units(tmp_path)

    def stop(*a, **k):
        raise SystemExit(f"stop {SENT}")
    monkeypatch.setattr(tl, "read_unit", stop)
    code, so, se = run(argv_of("olmo2-7b", units, pins, tmp_path / "rec.json"), capsys, pins)
    assert code == 2 and "SystemExit" in se and SENT not in se and so == ""
    assert not (tmp_path / "rec.json").exists()


def test_the_same_rows_in_another_order_pass(tmp_path, capsys):
    """C9: the units hold the same 200 ids; one file lists them in reverse order."""
    units, pins = three_units(tmp_path)
    m = KNOWN_MEANS[1103]
    lines = b"".join(json.dumps({"query_id": f"q-{k:03d}", "loss": m}).encode() + b"\n" for k in reversed(range(200)))
    folder, digest = make_unit(tmp_path / "x", "olmo2-7b", 1103, [m] * 200, loss_lines=lines)
    units[1103], pins[1103] = folder, digest
    code, so, se = run(argv_of("olmo2-7b", units, pins), capsys, pins)
    assert code == 0, se
