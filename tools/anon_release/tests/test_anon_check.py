"""Tests for anon_check.py. Secret-shaped values are assembled at run time, so this file holds none whole."""
import ast
import json
import os
import subprocess

import pytest

import anon_check as ac
import anon_export as ax
from conftest import REAL_REV, REAL_ROOT, make_config

FAKE = {
    "secret-hf_token": "hf" + "_" + "Ab3" * 12,
    "secret-github_token": "gh" + "p_" + "Z9y" * 9,
    "secret-github_pat": "github" + "_pat_" + "Q1w" * 9,
    "secret-runpod_key": "rp" + "a_" + "K7m" * 6,
    "secret-private_key": "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
    "secret-ssh_public_key": "ssh-" + "ed25519 AAAA" + "C3NzaC1lZDI1NTE5" + "AAAAI" + "x" * 40,
    "secret-anthropic_key": "sk-" + "ant-" + "api03-" + "R2d" * 10,
    "secret-openai_key": "sk-" + "proj-" + "T4b" * 12,
    "secret-aws_access_key": "AK" + "IA" + "ABCDEFGHIJKLMNOP",
    "secret-google_api_key": "AI" + "za" + "S" * 35,
    "secret-slack_token": "xo" + "xb-" + "1234567890-abc",
    "secret-credential_in_url": "https://" + "user:" + "pa55word" + "@host.example.org/x",
}

POSITIVE = [
    ("author-name", "Written by Rishi."),
    ("author-name", "rishi wrote"),
    ("email-own", "mail rishi.gh2002@gmail.com now"),
    ("email-any", "contact someone@university.edu"),
    ("github-handle", "user 4R4CN1D0"),
    ("github-owner-url", "https://github.com/4r4cn1d0/x"),
    ("repo-name", "4r4cn1d0/attribution"),
    ("macos-user", "home of spiderishi"),
    ("users-path", "/Users/someone/x"),
    ("local-time", "2026-10-17T19:10:00+05:30"),
    ("local-time", "19:10 IST"),
    ("local-time", "tz Asia/Kolkata"),
    ("agent-name", "the General Implementation chat"),
    ("agent-name", "GI VIII and GI I"),
    ("agent-name", "tmp/gi-vi-stage1/x.json"),
    ("agent-name", "the GPT lead"),
    ("agent-name", "Codex reviewed"),
    ("agent-name", "Claude Code"),
    ("agent-name", "CLAUDE.md"),
    ("agent-name", "an Opus worker"),
    ("agent-name", "on Fable 5.1"),
    ("agent-name", "Co-Authored-By: x"),
    ("substack", "see example.substack.com"),
    ("funder", "BlueDot Impact"),
    ("funder", "the LTFF and Manifund"),
]

NEGATIVE = [
    "token=False", "hf_hub_download(repo_id)", "revision a1847dff35000b4271fa70afc5db10fd29fedbdf",
    "/remote/runs/x", "src = 'import functools\\n\\n@functools.lru_cache\\ndef f(): pass'",
    "user.email=synthetic@example.invalid", "x@example.com", "y@host.test", "MISTY morning", "GIVE it",
    "opusculum", "Claudette", "fabled", "Rishikesh", "attribution-s1-a-1", "lambda x: x", "modal dialog",
    "SFFT transform", "a@b.T",
]


def hits_of(text):
    return {name for _, name in ac.scan_text(text, ac.compiled())}


@pytest.mark.parametrize("rule,text", POSITIVE)
def test_each_rule_fires(rule, text):
    assert rule in hits_of(text)


@pytest.mark.parametrize("rule,value", sorted(FAKE.items()))
def test_each_secret_shape_fires(rule, value):
    assert rule in hits_of(f"x = '{value}'")


@pytest.mark.parametrize("text", NEGATIVE)
def test_benign_look_alikes_pass(text):
    assert hits_of(text) == set()


def test_line_numbers():
    assert ac.scan_text("a\nb\nGI VI\n\nOpus", ac.compiled()) == [(3, "agent-name"), (5, "agent-name")]


def write_tree(root, files):
    for rel, data in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data if isinstance(data, bytes) else data.encode())


def test_report_lines_never_print_the_matched_text(tmp_path, capsys):
    tree = tmp_path / "t"
    secret = FAKE["secret-hf_token"]
    write_tree(tree, {"a/ok.py": "x = 1\n", "a/keys.py": f"\n\nTOKEN = '{secret}'\n",
                      "b/notes.md": "by Rishi (rishi.gh2002@gmail.com)\n"})
    report = tmp_path / "report.txt"
    assert ac.main([str(tree), "--report", str(report)]) == 1
    out, err = capsys.readouterr()
    assert out.splitlines() == ["a/keys.py:3:secret-hf_token", "b/notes.md:1:author-name", "b/notes.md:1:email-any",
                                "b/notes.md:1:email-own"]
    assert report.read_text() == out
    for leaked in (secret, "Rishi", "rishi.gh2002", "gmail"):
        assert leaked not in out and leaked not in err


def test_clean_tree_exits_0_and_usage_errors_exit_2(tmp_path):
    tree = tmp_path / "t"
    write_tree(tree, {"a.py": "x = 1\n"})
    assert ac.main([str(tree)]) == 0
    assert ac.main([str(tmp_path / "missing")]) == 2
    assert ac.main([str(tree), "--bogus"]) == 2
    report = tmp_path / "r.txt"
    report.write_text("old")
    assert ac.main([str(tree), "--report", str(report)]) == 2
    assert report.read_text() == "old"


def test_path_names_size_limit_symlinks_and_git_folder(tmp_path, capsys):
    tree = tmp_path / "t"
    write_tree(tree, {"gi-vi-notes/a.txt": "x\n", "docs/Rishi.md": "x\n", "big.json": "1" * 2000,
                      ".git/config": "[user]\n  name = Rishi\n"})
    os.symlink("big.json", tree / "link.json")
    assert ac.main([str(tree), "--size-limit", "1000"]) == 1
    out, err = capsys.readouterr()
    assert set(out.splitlines()) == {"gi-vi-notes:0:agent-name", "docs/Rishi.md:0:author-name",
                                     "big.json:0:size-limit", "link.json:0:symlink"}
    assert "not scanned: .git" in err


def test_config_size_limit_and_extra_rules(tmp_path, capsys):
    tree = tmp_path / "t"
    write_tree(tree, {"a.txt": "x" * 50 + "\nAcme Foundation\n"})
    config = tmp_path / "c.json"
    config.write_text(json.dumps({"size_limit_bytes": 10, "check_extra": [{"id": "extra-funder",
                                                                           "pattern": "Acme Foundation"}]}))
    assert ac.main([str(tree), "--config", str(config)]) == 1
    assert capsys.readouterr().out.splitlines() == ["a.txt:0:size-limit", "a.txt:2:extra-funder"]


def test_accepted_entries_need_the_exact_count_and_stale_ones_fail(tmp_path, capsys):
    tree = tmp_path / "t"
    write_tree(tree, {"a.md": "GI VI\nGI V\n", "b.md": "GI IV\n"})
    accept = tmp_path / "accept.json"

    def check(items):
        accept.write_text(json.dumps({"accepted": items}))
        code = ac.main([str(tree), "--accept", str(accept)])
        out, err = capsys.readouterr()
        return code, out.splitlines(), err

    a2 = {"path": "a.md", "rule": "agent-name", "count": 2, "reason": "frozen text"}
    code, out, err = check([a2])
    assert (code, out) == (1, ["b.md:1:agent-name"]) and "accepted: 2" in err
    code, out, err = check([a2, {"path": "b.md", "rule": "agent-name", "count": 1, "reason": "test data"}])
    assert (code, out) == (0, [])
    code, out, err = check([{**a2, "count": 1}])                      # a count that no longer matches fails
    assert code == 1 and "a.md:1:agent-name" in out and "a.md:2:agent-name" in out
    assert "expected 1, found 2" in err
    code, out, err = check([a2, {"path": "gone.md", "rule": "agent-name", "count": 1, "reason": "old"}])
    assert code == 1 and "gone.md:0:accept-stale" in out
    accept.write_text(json.dumps([{"path": "a.md", "rule": "agent-name", "count": 2}]))   # no reason
    assert ac.main([str(tree), "--accept", str(accept)]) == 2


def test_the_config_accepted_list_is_read(tmp_path, capsys):
    tree = tmp_path / "t"
    write_tree(tree, {"a.md": "GI VI\n"})
    config = tmp_path / "c.json"
    config.write_text(json.dumps({"accepted": [{"path": "a.md", "rule": "agent-name", "count": 1, "reason": "x"}]}))
    assert ac.main([str(tree), "--config", str(config)]) == 0


@pytest.mark.skipif(not (REAL_ROOT / ".git").exists(), reason="the main checkout is not available")
def test_secret_patterns_match_the_repository_source():
    """The copied patterns equal runkit/stage1-olmo/secret_scan.py PATTERNS at the pinned revision (read from git,
    parsed with ast, never imported)."""
    src = subprocess.run(["git", "-C", str(REAL_ROOT), "show", f"{REAL_REV}:runkit/stage1-olmo/secret_scan.py"],
                         capture_output=True, check=True).stdout.decode()
    tree = ast.parse(src)
    patterns = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PATTERNS" for t in node.targets):
            patterns = {k.value: v.args[0].value for k, v in zip(node.value.keys, node.value.values)}
    assert patterns == ac.SECRET_SCAN_PATTERNS


def test_export_then_check_reports_only_withheld_matches(repo, tmp_path, capsys):
    """End to end: what the exporter redacts, the checker no longer finds; what it withholds, the checker reports."""
    repo.write("pkg/m.py", '"""Written for GI VI by Rishi."""\nROOT = "/Users/spiderishi/Coding/attribution"\n')
    repo.write("docs/a.md", "BlueDot funded; 19:10 IST; an Opus worker.\n")
    repo.write("pkg/c.json", '{"note": "GI III"}\n')
    repo.commit()
    out, report = tmp_path / "out", tmp_path / "report.json"
    assert ax.main(["--root", str(repo.path), "--rev", "HEAD", "--config", str(make_config(tmp_path)),
                    "--out", str(out), "--report", str(report)]) == 0
    capsys.readouterr()
    assert ac.main([str(out)]) == 1
    lines = set(capsys.readouterr().out.splitlines())
    assert lines == {"pkg/m.py:2:macos-user", "pkg/m.py:2:users-path", "pkg/c.json:1:agent-name"}
    withheld = {(w["path"], w["line"]) for w in json.loads(report.read_text())["withheld"]}
    assert withheld == {("pkg/m.py", 2), ("pkg/c.json", 1)}
