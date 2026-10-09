"""sp_fiction_screen.sh, run as a copy whose Python is a recorder and whose HOME is empty (so no secrets file can be
sourced and nothing can reach RunPod): the arguments each command passes, the printed TAG, LIMIT and RESUME, and the
refusals (LIMIT on a launch, a missing refill SHA-256, a bad round)."""
from __future__ import annotations

import os
import pathlib
import shutil
import stat
import subprocess

import pytest
from conftest import HERE

SCRIPT = HERE.parent / "sp_fiction_screen.sh"
FAKE_PY = """#!/bin/bash
printf '%s\\n' "$*" >> "$ARGV_LOG"
echo "token=${HF_TOKEN:-}${HUGGING_FACE_HUB_TOKEN:-}" >> "$ARGV_LOG"
exit 0
"""


@pytest.fixture
def script(tmp_path):
    if not SCRIPT.is_file():
        pytest.skip("the launch script is not beside the tests")
    text = SCRIPT.read_text()
    for line, value in (("ROOT=/Users/spiderishi/Coding/attribution", f"ROOT={tmp_path}/root"),
                        ("W=$ROOT/.claude/worktrees/peaceful-jepsen-8b8eee", f"W={tmp_path}/w"),
                        ("K=$ROOT/tmp/family-probe-sp-fiction-screen", f"K={tmp_path}/k"),
                        ("PY=$ROOT/tmp/minimal-experiment-20261002/venv/bin/python", f"PY={tmp_path}/fakepy")):
        assert text.count(line + "\n") == 1, line
        text = text.replace(line + "\n", value + "\n")
    copy = tmp_path / "sp_fiction_screen.sh"
    copy.write_text(text)
    fake = tmp_path / "fakepy"
    fake.write_text(FAKE_PY)
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    (tmp_path / "home").mkdir()
    return copy


def run(script, *args, **env_over):
    tmp = script.parent
    log = tmp / "argv.log"
    log.unlink(missing_ok=True)
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp / "home"), "ARGV_LOG": str(log), "HF_TOKEN": "hf_" + "T" * 34,
           **env_over}
    done = subprocess.run(["bash", str(script), *args], env=env, capture_output=True, text=True, timeout=60)
    argv = log.read_text().splitlines() if log.exists() else []
    return done, argv


def test_bundle_prints_its_settings_and_passes_the_round_one_arguments(script):
    k = script.parent / "k"
    done, argv = run(script, "bundle", "1")
    assert done.returncode == 0
    assert "sp_fiction_screen: bundle round 1 tag sp-fiction-screen-r1 limit none resume none" in done.stderr
    assert argv[0] == f"-B {k}/tool/screen_pod.py bundle --tag sp-fiction-screen-r1 --round 1 --out {k}/dry/sp-fiction-screen-r1"
    done, argv = run(script, "bundle", "1", LIMIT="5", TAG="sp-fiction-screen-r1x")
    assert "tag sp-fiction-screen-r1x limit 5 resume none" in done.stderr
    assert argv[0].endswith("--tag sp-fiction-screen-r1x --round 1 --limit 5 --out " + f"{k}/dry/sp-fiction-screen-r1x")


def test_a_limit_on_a_launch_is_refused_before_anything_runs(script):
    done, argv = run(script, "launch", "1", LIMIT="20")
    assert done.returncode == 2 and argv == []
    assert "limit 20" in done.stderr and "refused: LIMIT is for dry checks" in done.stderr


@pytest.mark.skipif(not shutil.which("caffeinate"), reason="caffeinate is macOS only")
def test_launch_passes_tag_and_resume_and_no_token(script):
    k = script.parent / "k"
    done, argv = run(script, "launch", "1", TAG="sp-new", RESUME="sp-old")
    assert done.returncode == 0
    assert "launch round 1 tag sp-new limit none resume sp-old" in done.stderr
    assert argv == [f"-B {k}/tool/screen_pod.py launch --tag sp-new --round 1 --resume-from {k}/runs/sp-old", "token="]


def test_round_two_needs_the_refill_sha_and_names_the_refill_file(script):
    k, w = script.parent / "k", script.parent / "w"
    done, argv = run(script, "bundle", "2")
    assert done.returncode == 2 and argv == [] and "needs the refill file's SHA-256" in done.stderr
    done, argv = run(script, "bundle", "2", "a" * 64)
    assert argv[0] == (f"-B {k}/tool/screen_pod.py bundle --tag sp-fiction-screen-r2 --round 2 --refill "
                       f"{w}/tmp/side-fiction/screen/refill-r2.jsonl --refill-sha256 {'a' * 64} --out "
                       f"{k}/dry/sp-fiction-screen-r2")
    done, argv = run(script, "bundle", "4")
    assert done.returncode == 2 and argv == []


def test_summarize_and_final_reads_write_to_the_worktree_screen_folder(script):
    k, w = script.parent / "k", script.parent / "w"
    done, argv = run(script, "summarize", "1")
    assert argv[0] == (f"-B {k}/tool/screen_pod.py summarize --from {k}/runs/sp-fiction-screen-r1 --out "
                       f"{w}/tmp/side-fiction/screen")
    done, argv = run(script, "final-reads")
    assert argv[0] == (f"-B {k}/tool/screen_pod.py final-reads --final-dir {w}/tmp/side-fiction/final --screen-dir "
                       f"{w}/tmp/side-fiction/screen")
    assert os.environ.get("ARGV_LOG") is None                                 # the test's own environment untouched
