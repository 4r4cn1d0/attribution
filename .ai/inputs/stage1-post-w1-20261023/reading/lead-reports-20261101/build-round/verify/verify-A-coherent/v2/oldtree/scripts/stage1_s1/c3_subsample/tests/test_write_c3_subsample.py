"""write_c3_subsample.py on synthetic prepared folders (built as the engine's own tests build them): the committed
settings and their pin, the rule (the first 16 items in the file's own order, copied whole), the file's format, the
reads (manifest and dev bank only), every refusal, the text-free record and the CLI's new-file rules. The expected
items are parsed from banks/dev.jsonl independently of the writer."""

from __future__ import annotations

import builtins
import io
import json
import shutil
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes, sha256_file
from scripts.stage1 import s1common as s1
from scripts.stage1_s1.c3_subsample import write_c3_subsample as wc

import c3fixtures as cx
from c3guard import guarded

P_PIN = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"


@pytest.fixture(scope="module")
def p17(tmp_path_factory):
    return cx.build_p(tmp_path_factory.mktemp("p17"), harm=5, over=4)


@pytest.fixture(scope="module")
def p16(tmp_path_factory):
    return cx.build_p(tmp_path_factory.mktemp("p16"), harm=4, over=4)


@pytest.fixture(scope="module")
def p12(tmp_path_factory):
    return cx.build_p(tmp_path_factory.mktemp("p12"))


@pytest.fixture(scope="module")
def built(p17):
    """Guarded (c3guard): the writer's (file, record) on the 17-item P."""
    return guarded("built", lambda: cx.build(*p17))


def doc_of(built) -> dict:
    return json.loads(built[0])


def rec_of(built) -> dict:
    return json.loads(built[1])


def texts_of(items: list[dict]) -> list[str]:
    out = []
    for item in items:
        for key in ("prompt", "question"):
            if isinstance(item.get(key), str) and len(item[key]) >= 6:
                out.append(item[key])
        out += [t for t in item.get("texts", []) if isinstance(t, str) and len(t) >= 6]
    return out


# ----- the committed settings ---------------------------------------------------------------------------------------


def test_the_committed_settings_hash_to_the_literal_pin_and_name_p_16_dev_and_development():
    assert sha256_file(wc.SETTINGS_PATH) == wc.SETTINGS_SHA256
    settings, digest = s1.load_settings(wc.SETTINGS_PATH, wc.SETTINGS_SHA256, wc.SETTINGS_NAME)
    assert digest == wc.SETTINGS_SHA256
    assert settings["prepared_manifest_sha256"] == P_PIN
    assert settings["n_items"] == 16 and settings["source_bank"] == "dev" and settings["role"] == "development"
    assert settings["label_entries"] == {} and settings["engine_x"] == code_identity()["sha256"]
    assert wc.check_c3_settings(settings) is settings


def test_a_settings_file_that_differs_by_one_byte_refuses(tmp_path):
    path = tmp_path / "s.json"
    path.write_bytes(wc.SETTINGS_PATH.read_bytes().replace(b'"n_items": 16', b'"n_items": 15'))
    with pytest.raises(s1.Refusal, match="hash to"):
        s1.load_settings(path, wc.SETTINGS_SHA256, wc.SETTINGS_NAME)


@pytest.mark.parametrize("change, match", [
    ({"n_items": 0}, "positive integer"), ({"n_items": True}, "positive integer"), ({"n_items": "16"}, "positive"),
    ({"source_bank": "hidden"}, "dev-sourced"), ({"source_bank": "selector"}, "dev-sourced"),
    ({"role": "edit_confirmation"}, "development role only"), ({"prepared_manifest_sha256": "9ed6"}, "not a SHA-256"),
    ({"draw_label": ""}, "draw_label"), ({"rule": ""}, "rule"), ({"engine_x": "0" * 64}, "written for engine"),
])
def test_each_settings_field_is_checked(p17, change, match):
    with pytest.raises(s1.Refusal, match=match):
        cx.build(*p17, **change)


# ----- the rule and the format --------------------------------------------------------------------------------------


def test_the_file_lists_the_first_16_dev_items_in_file_order_each_copied_whole(p17, built):
    folder, _ = p17
    lines = cx.dev_lines(folder)
    assert len(lines) == 17
    doc = doc_of(built)
    assert doc["items"] == lines[:16]
    assert [i["prompt_id"] for i in doc["items"]] == [i["prompt_id"] for i in lines[:16]]


def test_the_rule_follows_the_files_own_line_order_not_a_sort(p17, tmp_path):
    folder, _ = p17
    shuffled, sha = cx.rewrite_dev(folder, tmp_path / "p", lambda items: items[::-1])
    lines = cx.dev_lines(shuffled)
    assert [i["prompt_id"] for i in lines] != sorted(i["prompt_id"] for i in lines)
    doc = json.loads(cx.build(shuffled, sha)[0])
    assert doc["items"] == lines[:16]


def test_the_file_has_engine_y_s_schema_and_canonical_bytes(p17, built):
    folder, sha = p17
    data, _ = built
    doc = doc_of(built)
    manifest = json.loads((folder / "manifest.json").read_bytes())
    assert canonical_json(doc) == data
    assert sorted(doc) == ["counts", "draw", "items", "kind", "source", "tokenizer", "version"]
    assert (doc["kind"], doc["version"]) == ("safety-selection bank subsample", 1)
    tok = manifest["data_config"]["tokenizer"]
    assert doc["tokenizer"] == {"repo_id": tok["repo_id"], "revision": tok["revision"]}
    assert doc["source"] == {"manifest_sha256": sha, "bank": "dev",
                             "bank_file_sha256": sha256_file(folder / "banks/dev.jsonl")}
    assert doc["source"]["bank_file_sha256"] == manifest["files"]["banks/dev.jsonl"]
    assert doc["draw"] == {"label": cx.committed()["draw_label"], "script_sha256": sha256_file(Path(wc.__file__)),
                           "settings_sha256": "5" * 64}
    counts: dict[str, int] = {}
    for item in cx.dev_lines(folder)[:16]:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    assert doc["counts"] == counts and sum(counts.values()) == 16


def test_exactly_16_items_is_enough_and_the_file_then_holds_the_whole_bank(p16):
    folder, sha = p16
    assert len(cx.dev_lines(folder)) == 16
    assert json.loads(cx.build(folder, sha)[0])["items"] == cx.dev_lines(folder)


def test_the_output_is_the_same_bytes_on_every_run(p17, built):
    assert cx.build(*p17) == tuple(built)


# ----- what is read -------------------------------------------------------------------------------------------------


def test_only_the_manifest_and_the_dev_bank_are_read(p17, built, tmp_path):
    folder, sha = p17
    bare = tmp_path / "bare"
    bare.mkdir()
    for name in ("manifest.json", "manifest.sha256", "banks/dev.jsonl"):
        (bare / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(folder / name, bare / name)
    assert cx.build(bare, sha) == tuple(built)          # no hidden, selector, engine, auditor or selector-view file


def test_no_file_of_p_other_than_the_manifest_and_the_dev_bank_is_opened(p17, monkeypatch):
    folder, sha = p17
    root = folder.resolve()
    opened: list[str] = []
    real_open, real_read = builtins.open, Path.read_bytes

    def spy_open(file, *args, **kwargs):
        path = Path(file).resolve() if isinstance(file, (str, Path)) else None
        if path is not None and root in path.parents:
            opened.append(path.relative_to(root).as_posix())
        return real_open(file, *args, **kwargs)

    def spy_read(self):
        if root in self.resolve().parents:
            opened.append(self.resolve().relative_to(root).as_posix())
        return real_read(self)

    monkeypatch.setattr(builtins, "open", spy_open)
    monkeypatch.setattr(Path, "read_bytes", spy_read)
    cx.build(folder, sha)
    assert opened and set(opened) <= {"manifest.json", "manifest.sha256", "banks/dev.jsonl"}
    assert "banks/dev.jsonl" in opened and "manifest.json" in opened


# ----- refusals -----------------------------------------------------------------------------------------------------


def test_fewer_than_16_dev_items_refuse(p12):
    folder, sha = p12
    assert len(cx.dev_lines(folder)) == 12
    with pytest.raises(s1.Refusal, match="holds 12 items, fewer than the 16"):
        cx.build(folder, sha)


def test_a_manifest_other_than_the_pinned_one_refuses(p17, p16):
    with pytest.raises(s1.Refusal, match="does not verify"):
        wc.build(prepared_root=p17[0], settings=cx.settings_for(p16[1]), settings_sha256="5" * 64)


def test_the_committed_pin_refuses_a_synthetic_p(p17):
    with pytest.raises(s1.Refusal, match="does not verify"):
        wc.build(prepared_root=p17[0], settings=cx.committed(), settings_sha256="5" * 64)


def test_a_manifest_that_differs_from_its_frozen_hash_refuses(p17, tmp_path):
    folder, sha = p17
    copy_ = tmp_path / "p"
    shutil.copytree(folder, copy_)
    (copy_ / "manifest.sha256").write_text("0" * 64 + "\n", encoding="ascii")
    with pytest.raises(s1.Refusal, match="does not verify"):
        cx.build(copy_, sha)


def test_a_dev_bank_that_differs_from_the_manifest_refuses(p17, tmp_path):
    folder, sha = p17
    copy_ = tmp_path / "p"
    shutil.copytree(folder, copy_)
    data = (copy_ / "banks/dev.jsonl").read_bytes()
    (copy_ / "banks/dev.jsonl").write_bytes(data.replace(b'"kind": "harm"', b'"kind": "harm "', 1))
    with pytest.raises(s1.Refusal, match="does not verify"):
        cx.build(copy_, sha)


def test_a_missing_dev_bank_refuses(p17, tmp_path):
    folder, sha = p17
    copy_ = tmp_path / "p"
    shutil.copytree(folder, copy_)
    (copy_ / "banks/dev.jsonl").unlink()
    with pytest.raises(s1.Refusal, match="does not verify"):
        cx.build(copy_, sha)


@pytest.mark.parametrize("transform, match", [
    (lambda items: items[:5] + [dict(items[5], prompt_id=items[2]["prompt_id"])] + items[6:], "item 5: its prompt_id is repeated"),
    (lambda items: items[:15] + [dict(items[16], prompt_id=items[0]["prompt_id"])], "item 15: its prompt_id is repeated"),
    (lambda items: items[:16] + [dict(items[16], prompt_id=items[0]["prompt_id"])], "item 16: its prompt_id is repeated"),
    (lambda items: items[:3] + [{k: v for k, v in items[3].items() if k != "kind"}] + items[4:], "item 3: no non-empty"),
    (lambda items: items[:3] + [dict(items[3], prompt_id="")] + items[4:], "item 3: no non-empty"),
    (lambda items: items[:3] + [dict(items[3], kind=7)] + items[4:], "item 3: no non-empty"),
])
def test_a_dev_bank_with_a_repeated_or_missing_id_or_kind_refuses(p17, tmp_path, transform, match):
    folder, sha = cx.rewrite_dev(p17[0], tmp_path / "p", transform)
    with pytest.raises(s1.Refusal, match=match):
        cx.build(folder, sha)


# ----- the record ---------------------------------------------------------------------------------------------------


def test_the_record_holds_the_hash_the_rule_the_count_and_ps_manifest(p17, built):
    folder, sha = p17
    data, _ = built
    rec, doc = rec_of(built), doc_of(built)
    assert rec["kind"] == "stage1 c3 subsample record" and rec["role"] == "development"
    assert rec["subsample"] == {"file_sha256": sha256_bytes(data), "bank": "subsample-" + sha256_bytes(data),
                                "bytes": len(data), "items": 16, "counts": doc["counts"]}
    assert rec["rule"] == cx.committed()["rule"] and rec["reference"] == cx.committed()["reference"]
    assert rec["prepared_manifest_sha256"] == sha and rec["dev_bank_items"] == 17
    assert rec["source"] == doc["source"] and rec["draw"] == doc["draw"] and rec["tokenizer"] == doc["tokenizer"]
    prov = rec["provenance"]
    assert prov["script_sha256"] == sha256_file(Path(wc.__file__)) == doc["draw"]["script_sha256"]
    assert prov["settings_sha256"] == "5" * 64 and prov["label_entries"] == {}
    assert prov["inputs"] == {"prepared_manifest": sha, "dev_bank": doc["source"]["bank_file_sha256"]}


def test_the_record_holds_no_id_and_no_text(p17, built):
    _, record = built
    lines = cx.dev_lines(p17[0])
    assert not any(i["prompt_id"].encode() in record for i in lines)
    texts = texts_of(lines)
    assert texts and not any(t.encode() in record for t in texts)
    assert not any(json.dumps(t)[1:-1].encode() in record for t in texts)


def test_a_record_that_would_hold_an_item_text_refuses(p17, tmp_path):
    folder, _ = p17
    repo = json.loads((folder / "manifest.json").read_bytes())["data_config"]["tokenizer"]["repo_id"]
    assert len(repo) >= 6
    leaky, sha = cx.rewrite_dev(folder, tmp_path / "p", lambda items: [dict(items[0], note=[repo])] + items[1:])
    with pytest.raises(s1.Refusal, match="would hold dev-bank text"):
        cx.build(leaky, sha)


def test_the_text_scan_covers_nested_values_and_skips_ids_kinds_and_hashes():
    items = [{"prompt_id": "p-0123456789abcdef", "kind": "overrefusal", "token_sha256": "a" * 64,
              "prompt": "a long prompt", "texts": ["choice one", "short"], "labels": ["A"], "extra": {"deep": "nested text"},
              "other": "overrefusal"}]
    assert sorted(wc.item_texts(items)) == ["A", "a long prompt", "choice one", "nested text", "short"]


# ----- the CLI ------------------------------------------------------------------------------------------------------


def cli(argv) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = wc.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def scaled(p17, tmp_path, monkeypatch):
    """The committed settings with the synthetic P's pin, written to a file whose SHA-256 the module pins for the test."""
    folder, sha = p17
    path = tmp_path / "settings.json"
    monkeypatch.setattr(wc, "SETTINGS_SHA256", cx.write_settings(path, cx.settings_for(sha)))
    return folder, path


def test_the_cli_writes_the_file_and_the_record_and_prints_hashes_only(scaled, built, tmp_path):
    folder, settings = scaled
    out, record = tmp_path / "tmp" / "c3" / "c3.json", tmp_path / "rec" / "c3_record.json"
    code, stdout, stderr = cli(["--prepared", folder, "--out", out, "--record", record, "--settings", settings])
    assert code == 0, stderr
    data = out.read_bytes()
    assert json.loads(data)["items"] == json.loads(built[0])["items"]
    rec = json.loads(record.read_bytes())
    assert rec["draw"]["settings_sha256"] == sha256_file(settings) == json.loads(data)["draw"]["settings_sha256"]
    assert rec["subsample"]["file_sha256"] == sha256_bytes(data)
    assert f"evaluate_bank subsample-{sha256_bytes(data)}" in stdout and sha256_file(record) in stdout
    assert not any(t in stdout for t in texts_of(cx.dev_lines(folder)))
    assert sorted(p.name for p in out.parent.iterdir()) == ["c3.json"]       # no temporary file left


def test_the_cli_never_overwrites_either_output(scaled, tmp_path):
    folder, settings = scaled
    out, record = tmp_path / "tmp" / "c3.json", tmp_path / "c3_record.json"
    assert cli(["--prepared", folder, "--out", out, "--record", record, "--settings", settings])[0] == 0
    before = (out.read_bytes(), record.read_bytes())
    code, _, stderr = cli(["--prepared", folder, "--out", out, "--record", record, "--settings", settings])
    assert code == 2 and "exists" in stderr and "nothing written" in stderr
    assert (out.read_bytes(), record.read_bytes()) == before
    other = tmp_path / "tmp" / "c3b.json"
    code, _, stderr = cli(["--prepared", folder, "--out", other, "--record", record, "--settings", settings])
    assert code == 2 and "exists" in stderr and not other.exists()


@pytest.mark.parametrize("where, reason", [("out_not_in_tmp", "folder named tmp"), ("same_path", "the same path"),
                                           ("out_in_p", "inside the prepared folder"),
                                           ("record_in_p", "inside the prepared folder"), ("out_is_symlink", "exists")])
def test_the_cli_refuses_bad_output_paths_and_writes_nothing(scaled, tmp_path, where, reason):
    folder, settings = scaled
    out, record = tmp_path / "tmp" / "c3.json", tmp_path / "c3_record.json"
    if where == "out_not_in_tmp":
        out = Path("/nonexistent-c3-root/public/c3.json")      # no folder named tmp (the scratch root has one)
    elif where == "same_path":
        record = out
    elif where == "out_in_p":
        out = folder / "tmp" / "c3.json"
    elif where == "record_in_p":
        record = folder / "c3_record.json"
    else:
        out.parent.mkdir(parents=True)
        out.symlink_to(tmp_path / "nowhere.json")
    code, _, stderr = cli(["--prepared", folder, "--out", out, "--record", record, "--settings", settings])
    assert code == 2 and "REFUSED" in stderr and reason in stderr and "nothing written" in stderr
    assert not record.exists() and (where == "out_is_symlink" or not out.exists())
    assert not (tmp_path / "nowhere.json").exists()


def test_the_cli_with_the_committed_settings_refuses_a_synthetic_p(p17, tmp_path):
    out, record = tmp_path / "tmp" / "c3.json", tmp_path / "c3_record.json"
    code, _, stderr = cli(["--prepared", p17[0], "--out", out, "--record", record])
    assert code == 2 and "does not verify" in stderr and "nothing written" in stderr
    assert not out.exists() and not record.exists()


def test_the_cli_refuses_a_short_dev_bank_and_writes_nothing(p12, tmp_path, monkeypatch):
    folder, sha = p12
    path = tmp_path / "settings.json"
    monkeypatch.setattr(wc, "SETTINGS_SHA256", cx.write_settings(path, cx.settings_for(sha)))
    out, record = tmp_path / "tmp" / "c3.json", tmp_path / "c3_record.json"
    code, _, stderr = cli(["--prepared", folder, "--out", out, "--record", record, "--settings", path])
    assert code == 2 and "fewer than the 16" in stderr and "nothing written" in stderr
    assert not out.exists() and not record.exists()


def test_write_new_refuses_a_path_that_appears_before_the_link(tmp_path):
    path = tmp_path / "f.json"
    path.write_bytes(b"theirs")
    with pytest.raises(s1.Refusal, match="exists"):
        wc.write_new(path, b"ours")
    assert path.read_bytes() == b"theirs" and sorted(p.name for p in tmp_path.iterdir()) == ["f.json"]
    fresh = tmp_path / "sub" / "g.json"
    assert wc.write_new(fresh, b"ours") == sha256_bytes(b"ours") and fresh.read_bytes() == b"ours"
