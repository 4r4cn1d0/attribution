"""Tests for anon_export.py on throwaway git repositories (and one read-only check against the real repository)."""
import ast
import hashlib
import json
import os
import pathlib
import subprocess

import pytest

import anon_export as ax
from conftest import REAL_CONFIG, REAL_REV, REAL_ROOT, make_config


def run(repo, config, out, rev="HEAD", report=None):
    argv = ["--root", str(repo.path), "--rev", rev, "--config", str(config), "--out", str(out)]
    if report:
        argv += ["--report", str(report)]
    return ax.main(argv)


def manifest(out):
    return json.loads((out / "MANIFEST.json").read_text())


def entry(out, path):
    return next(f for f in manifest(out)["files"] if f["path"] == path)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------------------------------------- source and OUT
def test_reads_the_committed_tree_not_the_working_tree(repo, tmp_path):
    repo.write("pkg/a.md", "committed\n")
    repo.commit()
    repo.write("pkg/a.md", "edited in the working tree\n")
    repo.write("pkg/new.md", "untracked\n")
    out = tmp_path / "out"
    assert run(repo, make_config(tmp_path), out) == 0
    assert (out / "pkg/a.md").read_text() == "committed\n"
    assert not (out / "pkg/new.md").exists()


def test_rev_selects_an_older_commit(repo, tmp_path):
    repo.write("pkg/a.md", "one\n")
    first = repo.commit()
    repo.write("pkg/a.md", "two\n")
    repo.commit()
    out = tmp_path / "out"
    assert run(repo, make_config(tmp_path), out, rev=first) == 0
    assert (out / "pkg/a.md").read_text() == "one\n"
    assert manifest(out)["source_revision"] == first


def test_refuses_an_existing_out(repo, tmp_path, capsys):
    repo.write("pkg/a.md", "x\n")
    repo.commit()
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep.txt").write_text("mine")
    assert run(repo, make_config(tmp_path), out) == 2
    assert sorted(p.name for p in out.iterdir()) == ["keep.txt"]
    assert "OUT already exists" in capsys.readouterr().err


def test_refuses_out_inside_the_repository_and_report_inside_out(repo, tmp_path):
    repo.write("pkg/a.md", "x\n")
    repo.commit()
    config = make_config(tmp_path)
    assert run(repo, config, repo.path / "export") == 2
    assert not (repo.path / "export").exists()
    out = tmp_path / "out"
    assert run(repo, config, out, report=out / "r.json") == 2
    assert not out.exists()


def test_refuses_a_missing_exact_allow_entry_and_an_unused_glob(repo, tmp_path, capsys):
    repo.write("pkg/a.md", "x\n")
    repo.commit()
    assert run(repo, make_config(tmp_path, allow=["pkg/**", "pkg/missing.py"]), tmp_path / "o1") == 2
    assert run(repo, make_config(tmp_path, allow=["pkg/**", "nothing/**"]), tmp_path / "o2") == 2
    err = capsys.readouterr().err
    assert "pkg/missing.py" in err and "nothing/**" in err
    assert not (tmp_path / "o1").exists() and not (tmp_path / "o2").exists()


def test_refuses_a_bad_revision_and_a_bad_config(repo, tmp_path):
    repo.write("pkg/a.md", "x\n")
    repo.commit()
    assert run(repo, make_config(tmp_path), tmp_path / "o1", rev="no-such-rev") == 2
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"allow": ["pkg/**"], "deny": [], "size_limit_bytes": 10, "rules": [
        {"id": "r", "kind": "regex", "pattern": "x", "token": "lower"}]}))
    assert run(repo, bad, tmp_path / "o2") == 2


# ---------------------------------------------------------------------------------------------------- selection
def test_deny_wins_over_a_glob_but_not_over_an_exact_entry(repo, tmp_path):
    repo.write("pkg/a.py", "x = 1\n")
    repo.write("pkg/__pycache__/a.cpython-311.pyc", b"\x00\x01")
    repo.write("pkg/secret/keep.md", "k\n")
    repo.write("pkg/secret/drop.md", "d\n")
    repo.write(".ai/inputs/frozen.json", "{}\n")
    repo.write(".ai/inputs/sealed.json", "{}\n")
    repo.commit()
    config = make_config(tmp_path, allow=["pkg/**", "pkg/secret/keep.md", ".ai/inputs/frozen.json"],
                         deny=["**/__pycache__/**", "pkg/secret/**", ".ai/**"])
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, config, out, report=report) == 0
    got = sorted(f["path"] for f in manifest(out)["files"])
    assert got == [".ai/inputs/frozen.json", "pkg/a.py", "pkg/secret/keep.md"]
    detail = json.loads(report.read_text())
    assert detail["denied_by_glob"] == ["pkg/__pycache__/a.cpython-311.pyc", "pkg/secret/drop.md"]


def test_binary_non_utf8_oversize_and_symlink_are_skipped_and_listed(repo, tmp_path):
    repo.write("pkg/bin.dat", b"abc\x00def")
    repo.write("pkg/latin.txt", "caf\xe9".encode("latin-1"))
    repo.write("pkg/big.md", "x" * 20_000)
    repo.write("pkg/big-ok.json", "[" + "1," * 6000 + "1]")
    repo.write("pkg/a.md", "ok\n")
    os.symlink("a.md", repo.path / "pkg/link.md")
    repo.commit()
    config = make_config(tmp_path, size_exceptions=["pkg/big-ok.json"])
    out = tmp_path / "out"
    assert run(repo, config, out) == 0
    skipped = {s["path"]: s["reason"] for s in manifest(out)["skipped"]}
    assert skipped == {"pkg/bin.dat": "binary", "pkg/latin.txt": "not UTF-8", "pkg/big.md": "over size limit",
                       "pkg/link.md": "symlink"}
    assert (out / "pkg/big-ok.json").exists() and not (out / "pkg/big.md").exists()
    assert not (out / "pkg/link.md").exists()


def test_glob_semantics():
    rx = ax.glob_regex("pkg/**")
    assert rx.match("pkg/a.py") and rx.match("pkg/x/y/z.py") and not rx.match("pkgx/a.py")
    rx = ax.glob_regex("**/__pycache__/**")
    assert rx.match("__pycache__/a.pyc") and rx.match("a/b/__pycache__/c.pyc") and not rx.match("a/pycache/c")
    rx = ax.glob_regex("scripts/*.py")
    assert rx.match("scripts/a.py") and not rx.match("scripts/sub/a.py")


# ---------------------------------------------------------------------------------------------------- redaction
def test_prose_redaction_inserts_tokens_and_counts(repo, tmp_path):
    text = ("Written by Rishi (rishi.gh2002@gmail.com), github 4r4cn1d0, at /Users/spiderishi/Coding/attribution/tmp.\n"
            "Funded by BlueDot. Checked 13:40 UTC (19:10 IST) by an Opus worker for GI VI and General Implementation.\n"
            "Untouched: Rishikesh, GIVE, opusculum, MISTY.\n")
    repo.write("docs/note.md", text)
    repo.commit()
    out = tmp_path / "out"
    assert run(repo, make_config(tmp_path), out) == 0
    got = (out / "docs/note.md").read_text()
    assert got == ("Written by [AUTHOR] ([EMAIL]), github [HANDLE], at [PATH]/tmp.\n"
                   "Funded by [FUNDER]. Checked 13:40 UTC ([LOCAL-TIME]) by an [AGENT] worker for [AGENT] and [AGENT].\n"
                   "Untouched: Rishikesh, GIVE, opusculum, MISTY.\n")
    e = entry(out, "docs/note.md")
    assert e["redacted"] is True
    assert e["rule_counts"] == {"agent-name": 3, "author-name": 1, "checkout-path": 1, "email-own": 1, "funder": 1,
                                "github-handle": 1, "local-time": 1}
    assert e["source_sha256"] == sha(text.encode()) and e["exported_sha256"] == sha(got.encode())


def test_python_comments_and_docstrings_redacted_code_withheld(repo, tmp_path):
    src = ('"""Module by an Opus worker for GI VI."""\n'
           "import pathlib\n\n"
           "ROOT = pathlib.Path('/Users/spiderishi/Coding/attribution')   # set by GI III\n\n\n"
           "def f():\n"
           "    'helper written for GI IV'\n"
           "    return f'{ROOT}/claude'\n")
    repo.write("pkg/m.py", src)
    repo.commit()
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, make_config(tmp_path), out, report=report) == 0
    got = (out / "pkg/m.py").read_text()
    assert got == ('"""Module by an [AGENT] worker for [AGENT]."""\n'
                   "import pathlib\n\n"
                   "ROOT = pathlib.Path('/Users/spiderishi/Coding/attribution')   # set by [AGENT]\n\n\n"
                   "def f():\n"
                   "    'helper written for [AGENT]'\n"
                   "    return f'{ROOT}/claude'\n")
    assert ax.python_shape(got) == ax.python_shape(src)
    withheld = json.loads(report.read_text())["withheld"]
    assert {(w["line"], w["rule"], w["reason"]) for w in withheld} == {(4, "checkout-path", "code"),
                                                                        (9, "agent-name", "code")}
    assert all("text" not in w for w in withheld)


def test_unparseable_python_is_never_redacted(repo, tmp_path):
    src = "# by GI VI\ndef broken(:\n"
    repo.write("pkg/bad.py", src)
    repo.commit()
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, make_config(tmp_path), out, report=report) == 0
    assert (out / "pkg/bad.py").read_text() == src
    assert json.loads(report.read_text())["withheld"][0]["reason"] == "code-unparsed"


def test_non_prose_files_are_byte_identical(repo, tmp_path):
    for name, text in (("pkg/c.json", '{"purpose": "GI III round 5"}\n'), ("pkg/run.sh", "# by GI III\necho\n"),
                       ("pkg/req.txt", "torch==2.4  # GI III\n")):
        repo.write(name, text)
    repo.commit()
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, make_config(tmp_path), out, report=report) == 0
    for f in manifest(out)["files"]:
        assert f["source_sha256"] == f["exported_sha256"] and f["redacted"] is False
    reasons = {(w["path"], w["reason"]) for w in json.loads(report.read_text())["withheld"]}
    assert reasons == {("pkg/c.json", "not-prose"), ("pkg/run.sh", "not-prose"), ("pkg/req.txt", "not-prose")}


def test_ast_guard():
    assert ax.python_shape("x = 1  # GI VI\n") == ax.python_shape("x = 1  # [AGENT]\n")
    assert ax.python_shape('"""GI VI"""\nx = 1\n') == ax.python_shape('"""[AGENT]"""\nx = 1\n')
    assert ax.python_shape("x = 'GI VI'\n") != ax.python_shape("x = '[AGENT]'\n")


def test_ast_guard_aborts_the_export(repo, tmp_path, monkeypatch, capsys):
    repo.write("pkg/m.py", "x = 'GI VI'\n")
    repo.commit()

    def careless(path, text, matches, config, pinned):
        for m in matches:
            m["status"] = "applied"
    monkeypatch.setattr(ax, "classify", careless)
    assert run(repo, make_config(tmp_path), tmp_path / "out") == 1
    assert "syntax tree" in capsys.readouterr().err


# ------------------------------------------------------------------------------------------------------------- pins
def test_a_pinned_file_is_withheld_and_listed(repo, tmp_path):
    pinned_text = "Notes by GI VI.\n"
    repo.write("docs/pinned.md", pinned_text)
    repo.write("docs/prefix-pinned.md", "Also GI V.\n")
    repo.write("pkg/pins.py", "PINS = {'docs/pinned.md': '%s'}\nP = '%s'\n"
               % (sha(pinned_text.encode()), sha(b"Also GI V.\n")[:16]))
    repo.write("docs/free.md", "Free GI IV.\n")
    repo.commit()
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, make_config(tmp_path), out, report=report) == 0
    assert (out / "docs/pinned.md").read_text() == pinned_text
    assert (out / "docs/prefix-pinned.md").read_text() == "Also GI V.\n"
    assert (out / "docs/free.md").read_text() == "Free [AGENT].\n"
    detail = json.loads(report.read_text())
    assert set(detail["pinned_files_a_redaction_would_change"]) == {"docs/pinned.md", "docs/prefix-pinned.md"}
    assert detail["pinned"]["docs/prefix-pinned.md"] == [{"by": "pkg/pins.py", "count": 1, "hex_len": 16}]
    assert {w["reason"] for w in detail["withheld"]} == {"pinned"}


def test_path_keyed_pins_report_matches_and_stale_values(repo, tmp_path):
    repo.write("pkg/a.py", "x = 1\n")
    repo.write("pkg/b.py", "y = 2\n")
    repo.write("pkg/pins.json", json.dumps({"files": {"pkg/a.py": sha(b"x = 1\n")},
                                            "entries": [{"path": "pkg/b.py", "role": "code", "sha256": "0" * 64}]}))
    repo.commit()
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, make_config(tmp_path), out, report=report) == 0
    keyed = {(r["file"], r["matches_rev"]) for r in json.loads(report.read_text())["path_keyed_pins"]}
    assert keyed == {("pkg/a.py", True), ("pkg/b.py", False)}


def test_byte_identical_and_rule_subset(repo, tmp_path):
    frozen = "Frozen by GI VI, funded by BlueDot.\n"
    osf = "Written 13:40 UTC (19:10 IST) by GI VI at /Users/spiderishi/Coding/attribution; BlueDot line.\n"
    repo.write("docs/frozen.md", frozen)
    repo.write("docs/osf.md", osf)
    repo.commit()
    config = make_config(tmp_path, byte_identical=["docs/frozen.md"],
                         redact_pinned={"docs/osf.md": ["checkout-path", "funder", "local-time"]})
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, config, out, report=report) == 0
    assert (out / "docs/frozen.md").read_text() == frozen
    assert (out / "docs/osf.md").read_text() == \
        "Written 13:40 UTC ([LOCAL-TIME]) by GI VI at [PATH]; [FUNDER] line.\n"
    reasons = {(w["path"], w["rule"], w["reason"]) for w in json.loads(report.read_text())["withheld"]}
    assert reasons == {("docs/frozen.md", "agent-name", "byte-identical"), ("docs/frozen.md", "funder", "byte-identical"),
                       ("docs/osf.md", "agent-name", "outside-rule-subset")}


def test_a_mutation_anchor_keeps_its_comment(repo, tmp_path):
    repo.write("pkg/m.py", "x = 1  # GI VI round 2: keep\ny = 2  # GI VI elsewhere\n")
    repo.write("pkg/mutation/mutants.json", json.dumps(
        {"mutants": [{"id": "m1", "file": "pkg/m.py", "find": "x = 1  # GI VI round 2", "replace": "x = 2"}]}))
    repo.write("pkg/run_mutants.py", "SPEC = {'file': 'm.py', 'find': 'y = 2  # GI', 'replace': 'y = 3'}\n")
    repo.write("pkg/other.py", "z = 1  # GI VI\n")
    repo.commit()
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, make_config(tmp_path), out, report=report) == 0
    assert (out / "pkg/m.py").read_text() == "x = 1  # GI VI round 2: keep\ny = 2  # GI VI elsewhere\n"
    assert (out / "pkg/other.py").read_text() == "z = 1  # [AGENT]\n"
    rows = [w for w in json.loads(report.read_text())["withheld"] if w["path"] == "pkg/m.py"]
    assert sorted((w["line"], w["reason"], w["anchored_by"]) for w in rows) == [
        (1, "mutation-anchor", "pkg/mutation/mutants.json"), (2, "mutation-anchor", "pkg/run_mutants.py")]


# --------------------------------------------------------------------------------------------- manifest and output
def test_manifest_hashes_match_git_and_disk_and_readme_lists_frozen(repo, tmp_path):
    repo.write("pkg/a.md", "by GI VI\n")
    repo.write("pkg/b.py", "x = 1\n")
    repo.write("pkg/tool.sh", "#!/bin/sh\necho hi\n", mode=0o755)
    repo.commit()
    config = make_config(tmp_path, frozen={"pkg/b.py": "a frozen file"}, byte_identical=["pkg/b.py"])
    out = tmp_path / "out"
    assert run(repo, config, out) == 0
    m = manifest(out)
    assert m["file_count"] == 3 and m["hash"] == "SHA-256"
    for f in m["files"]:
        blob = subprocess.run(["git", "-C", str(repo.path), "show", f"HEAD:{f['path']}"], capture_output=True,
                              check=True).stdout
        assert f["source_sha256"] == sha(blob)
        assert f["exported_sha256"] == sha((out / f["path"]).read_bytes())
        assert f["redacted"] == (f["source_sha256"] != f["exported_sha256"])
    assert os.stat(out / "pkg/tool.sh").st_mode & 0o777 == 0o755
    assert os.stat(out / "pkg/a.md").st_mode & 0o777 == 0o644
    readme = (out / "EXPORT-README.md").read_text()
    assert f"| `pkg/b.py` | a frozen file | `{sha(b'x = 1' + bytes([10]))}` | yes |" in readme
    assert "shasum -a 256" in readme
    assert "A licence file is to be added" in readme


def test_deterministic(repo, tmp_path):
    repo.write("pkg/a.md", "by GI VI at 10:00 IST\n")
    repo.write("pkg/b.py", "# Opus\nx = 1\n")
    repo.write("pkg/c.bin", b"\x00\x01")
    repo.commit()
    config = make_config(tmp_path)
    a, b = tmp_path / "a", tmp_path / "b"
    assert run(repo, config, a) == 0 and run(repo, config, b) == 0

    def tree(root):
        return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
    assert tree(a) == tree(b)


def test_generated_files_hold_no_identity_strings(repo, tmp_path):
    import anon_check
    repo.write("docs/rishi-notes.md", "Rishi wrote this; GI VI checked it.\n")
    repo.commit()
    out = tmp_path / "out"
    assert run(repo, make_config(tmp_path), out) == 0
    rules = anon_check.compiled()
    for name in ("MANIFEST.json", "EXPORT-README.md"):
        hits = anon_check.scan_text((out / name).read_text(), rules)
        assert [h for h in hits if h[1] != "author-name"] == []
    # the file *name* holds the author's name: the checker must report it (path hit), the exporter cannot rename
    hits, _ = anon_check.scan_tree(str(out), 10_000, rules)
    assert ("docs/rishi-notes.md", 0, "author-name") in hits


# ------------------------------------------------------------------------------------- the real repository (read only)
@pytest.mark.skipif(not (REAL_ROOT / ".git").exists(), reason="the main checkout is not available")
def test_real_config_reproduces_the_osf_deposit_copies():
    """The two OSF-redacted frozen files, redacted with the shipped config, equal the deposit's anonymized copies
    byte for byte (HASHES.json anon_sha256). Reads three files from git at the pinned revision; writes nothing."""
    config = ax.load_config(str(REAL_CONFIG))

    def show(path):
        return subprocess.run(["git", "-C", str(REAL_ROOT), "show", f"{REAL_REV}:{path}"], capture_output=True,
                              check=True).stdout
    hashes = json.loads(show("research/experiments/2026-10-23-osf-deposit-package/HASHES.json"))
    checked = 0
    for item in hashes["files"]:
        if item["byte_identical_to_original"]:
            continue
        original = show(item["original_path"])
        assert sha(original) == item["original_sha256"]
        text = original.decode("utf-8")
        matches = ax.find_matches(text, config["rules"], prose=ax.is_prose(item["original_path"], config))
        ax.classify(item["original_path"], text, matches, config, pinned=True)
        anon = ax.apply(text, matches).encode("utf-8")
        assert sha(anon) == item["anon_sha256"], item["file"]
        assert sum(m["status"] == "applied" for m in matches) == item["redaction_count"]
        checked += 1
    assert checked == 2


# ------------------------------------------------------------------------------ lead decisions: paths, re-pins, accepts
CODE_OK_RULES = [
    {"id": "home-path-full", "kind": "regex", "pattern": "/Users/[A-Za-z0-9._-]+(?:/[^\\s\"'`()<>\\[\\]{},;|*]*)?",
     "token": "[PATH]", "scope": "non-prose", "code_ok": True},
    {"id": "checkout-path", "kind": "literal", "pattern": "/Users/spiderishi/Coding/attribution", "token": "[PATH]",
     "code_ok": True},
    {"id": "agent-name", "kind": "regex", "pattern": "(?<![A-Za-z])GI[ -](?:VI|V|IV|III)(?![A-Za-z])",
     "token": "[AGENT]"},
]


def test_code_ok_rules_reach_code_strings_and_settings_and_keep_the_syntax_tree(repo, tmp_path):
    src = ("import pathlib\n"
           "ROOT = pathlib.Path('/Users/spiderishi/Coding/attribution/tmp/x')   # GI VI\n"
           "NAME = 'GI VI'\n")
    repo.write("pkg/m.py", src)
    repo.write("pkg/run.sh", "PY=/Users/spiderishi/Coding/attribution/tmp/venv/bin/python\n")
    repo.write("pkg/c.json", '{"root": "/Users/someone/x", "note": "GI III"}\n')
    repo.write("docs/a.md", "K=/Users/spiderishi/Coding/attribution/scripts/x and GI IV\n")
    repo.commit()
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, make_config(tmp_path, rules=CODE_OK_RULES), out, report=report) == 0
    got = (out / "pkg/m.py").read_text()
    assert got == "import pathlib\nROOT = pathlib.Path('[PATH]')   # [AGENT]\nNAME = 'GI VI'\n"
    assert ax.python_shape(got, True) == ax.python_shape(src, True) and ax.python_shape(got) != ax.python_shape(src)
    assert (out / "pkg/run.sh").read_text() == "PY=[PATH]\n"
    assert (out / "pkg/c.json").read_text() == '{"root": "[PATH]", "note": "GI III"}\n'
    assert (out / "docs/a.md").read_text() == "K=[PATH]/scripts/x and [AGENT]\n"      # prose keeps the relative part
    reasons = {(w["path"], w["rule"], w["reason"]) for w in json.loads(report.read_text())["withheld"]}
    assert reasons == {("pkg/m.py", "agent-name", "code"), ("pkg/c.json", "agent-name", "not-prose")}


def test_the_every_string_guard_still_refuses_a_structural_change():
    assert ax.python_shape("x = 'a'\n", True) == ax.python_shape("x = 'b'\n", True)
    assert ax.python_shape("x = b'a'\n", True) == ax.python_shape("x = b'[PATH]'\n", True)
    assert ax.python_shape("x = 'a'\n", True) != ax.python_shape("y = 'a'\n", True)
    assert ax.python_shape("x = f'{a}/b'\n", True) == ax.python_shape("x = f'{a}/[PATH]'\n", True)


def test_repin_redacts_a_pinned_file_and_updates_the_quoted_hashes(repo, tmp_path):
    target = "ROOT = '/Users/spiderishi/Coding/attribution'\n"
    repo.write("pkg/common.py", target)
    old = sha(target.encode())
    repo.write("pkg/tests/test_pins.py", "REVIEWED = {'common.py': '%s'}\nSHORT = '%s'\n" % (old, old[:16]))
    repo.commit()
    config = make_config(tmp_path, rules=CODE_OK_RULES, repin=["pkg/common.py"])
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert run(repo, config, out, report=report) == 0
    new = sha((out / "pkg/common.py").read_bytes())
    assert (out / "pkg/common.py").read_text() == "ROOT = '[PATH]'\n"
    assert (out / "pkg/tests/test_pins.py").read_text() == "REVIEWED = {'common.py': '%s'}\nSHORT = '%s'\n" % (
        new, new[:16])
    m = manifest(out)
    assert m["repinned"] == [{"path": "pkg/common.py", "old_sha256": old, "new_sha256": new,
                              "updated_in": ["pkg/tests/test_pins.py"]}]
    assert entry(out, "pkg/tests/test_pins.py")["pins_updated"] == 2
    assert entry(out, "pkg/common.py")["exported_sha256"] == new


def test_without_repin_a_pinned_file_keeps_its_path(repo, tmp_path):
    target = "ROOT = '/Users/spiderishi/Coding/attribution'\n"
    repo.write("pkg/common.py", target)
    repo.write("pkg/pins.py", "P = '%s'\n" % sha(target.encode()))
    repo.commit()
    out = tmp_path / "out"
    assert run(repo, make_config(tmp_path, rules=CODE_OK_RULES), out) == 0
    assert (out / "pkg/common.py").read_text() == target and manifest(out)["repinned"] == []


def test_repin_refuses_a_frozen_pinner_and_a_pinned_pinner(repo, tmp_path, capsys):
    target = "ROOT = '/Users/spiderishi/Coding/attribution'\n"
    repo.write("pkg/common.py", target)
    pinner = "P = '%s'\n" % sha(target.encode())
    repo.write("pkg/pins.py", pinner)
    repo.write("docs/record.md", "the pins file: %s\n" % sha(pinner.encode()))
    repo.commit()
    config = make_config(tmp_path, rules=CODE_OK_RULES, repin=["pkg/common.py"])
    assert run(repo, config, tmp_path / "o1") == 1
    assert "pkg/pins.py changed but is pinned by ['docs/record.md']" in capsys.readouterr().err
    config = make_config(tmp_path, rules=CODE_OK_RULES, repin=["pkg/common.py"], byte_identical=["pkg/pins.py"])
    assert run(repo, config, tmp_path / "o2") == 1
    assert "pinned by the frozen file pkg/pins.py" in capsys.readouterr().err
    config = make_config(tmp_path, rules=CODE_OK_RULES, repin=["pkg/common.py", "pkg/pins.py"])
    assert run(repo, config, tmp_path / "o3") == 0                     # the chain is re-pinned in turn
    o3 = tmp_path / "o3"
    assert sha((o3 / "pkg/pins.py").read_bytes()) in (o3 / "docs/record.md").read_text()
    assert sha((o3 / "pkg/common.py").read_bytes()) in (o3 / "pkg/pins.py").read_text()


def test_accepted_entries_reach_the_manifest_and_must_name_exported_files(repo, tmp_path):
    repo.write("pkg/a.json", '{"note": "GI VI"}\n')
    repo.commit()
    item = {"path": "pkg/a.json", "rule": "agent-name", "count": 1, "reason": "a pinned settings file"}
    out = tmp_path / "out"
    assert run(repo, make_config(tmp_path, accepted=[item]), out) == 0
    assert entry(out, "pkg/a.json")["accepted"] == [{"rule": "agent-name", "count": 1, "reason": "a pinned settings file"}]
    assert run(repo, make_config(tmp_path, accepted=[{**item, "path": "pkg/missing.json"}]), tmp_path / "o2") == 2
    assert run(repo, make_config(tmp_path, accepted=[{**item, "reason": " "}]), tmp_path / "o3") == 2
    assert run(repo, make_config(tmp_path, accepted=[{**item, "count": 0}]), tmp_path / "o4") == 2
