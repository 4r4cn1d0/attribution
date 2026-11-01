"""Shared fixtures: a throwaway git repository built in tmp_path (no network, no global config written)."""
import json
import os
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS))

REAL_ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
REAL_REV = "d5f3993ce07ad4f0a562055e5cbd6c7deb431398"
REAL_CONFIG = TOOLS / "anon_export_config.json"


def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                           "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main", *args],
                          check=True, capture_output=True, env=env).stdout.decode().strip()


class Repo:
    def __init__(self, path: pathlib.Path):
        self.path = path
        path.mkdir()
        git(path, "init", "-q")

    def write(self, rel: str, data, mode: int | None = None):
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            data = data.encode("utf-8")
        target.write_bytes(data)
        if mode is not None:
            target.chmod(mode)
        return target

    def commit(self, message="c") -> str:
        git(self.path, "add", "-A")
        git(self.path, "commit", "-q", "-m", message)
        return git(self.path, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path / "repo")


BASE_RULES = [
    {"id": "email-own", "kind": "literal", "pattern": "rishi.gh2002@gmail.com", "ignore_case": True,
     "token": "[EMAIL]"},
    {"id": "checkout-path", "kind": "literal", "pattern": "/Users/spiderishi/Coding/attribution", "token": "[PATH]"},
    {"id": "home-path", "kind": "regex", "pattern": "/Users/[A-Za-z0-9._-]+", "token": "[PATH]"},
    {"id": "github-handle", "kind": "literal", "pattern": "4r4cn1d0", "ignore_case": True, "token": "[HANDLE]"},
    {"id": "macos-user", "kind": "literal", "pattern": "spiderishi", "ignore_case": True, "token": "[HANDLE]"},
    {"id": "author-name", "kind": "regex", "pattern": "(?<![A-Za-z0-9])Rishi(?![A-Za-z0-9])", "ignore_case": True,
     "token": "[AUTHOR]"},
    {"id": "funder", "kind": "regex", "pattern": "BlueDot(?: Impact)?|Manifund", "token": "[FUNDER]"},
    {"id": "local-time", "kind": "regex",
     "pattern": "[0-9]{1,2}:[0-9]{2}(?::[0-9]{2})? ?IST(?![A-Za-z])|\\+05:?30(?![0-9])", "token": "[LOCAL-TIME]"},
    {"id": "agent-name", "kind": "regex",
     "pattern": "General Implementation|(?<![A-Za-z])GI[ -](?:VIII|VII|VI|IV|V|III|II|I)(?![A-Za-z])|"
                "(?i:(?<![a-z])opus(?![a-z]))|(?i:(?<![a-z])claude(?![a-z]))", "token": "[AGENT]"},
]


def make_config(tmp_path, **overrides) -> pathlib.Path:
    config = {"allow": ["**"], "deny": ["**/__pycache__/**"], "size_limit_bytes": 10_000,
              "rules": BASE_RULES, "prose_globs": ["**/*.md"]}
    config.update(overrides)
    path = tmp_path / f"config-{len(list(tmp_path.glob('config-*.json')))}.json"
    path.write_text(json.dumps(config))
    return path
