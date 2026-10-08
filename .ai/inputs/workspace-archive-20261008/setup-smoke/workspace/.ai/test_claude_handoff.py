"""Offline checks for the pinned Claude handoff launcher.

Nothing here calls a model or needs Git, an installed Claude CLI, or the user's
login: ROOT is a throwaway directory and the CLI is a small fake script.
"""

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "handoff", Path(__file__).with_name("claude_handoff.py")
)
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)

SLEEPER = [sys.executable, "-c", "import time; time.sleep(60)"]
WATCHED_ENV = ["CODEX_CLAUDE_WORKER", "CLAUDE_CODE_EFFORT_LEVEL", "ANTHROPIC_API_KEY",
               "ANTHROPIC_MODEL"]
# Stands in for the Claude CLI: answers the version and login checks; for a worker
# call it records what it received, applies planned edits in its cwd and prints
# a canned result.
FAKE_CLI = """
import json, os, sys
from pathlib import Path
here = Path(__file__).parent
plan = json.loads((here / "plan.json").read_text())
args = sys.argv[1:]
if args == ["--version"]:
    print("2.1.300 (Claude Code)")
elif "auth" in args:
    print(json.dumps({"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty"}))
else:
    seen = {"argv": args, "stdin": sys.stdin.read(), "cwd": os.getcwd(),
            "env": {key: os.environ.get(key) for key in plan["watched_env"]}}
    (here / "seen.json").write_text(json.dumps(seen))
    for name, text in plan["write"].items():
        Path(name).write_text(text)
    print(json.dumps(plan["response"]))
"""


def args(**overrides):
    values = dict(mode="review", allow_bash=[], model=handoff.MODEL,
                  effort=handoff.EFFORT, max_turns=20)
    values.update(overrides)
    return argparse.Namespace(**values)


def option(command, name):
    return command[command.index(name) + 1]


def result(**overrides):
    value = {"type": "result", "subtype": "success", "is_error": False, "result": "done",
             "modelUsage": {"claude-opus-5-5": {"outputTokens": 1}},
             "permission_denials": [], "session_id": "session-1", "num_turns": 1}
    value.update(overrides)
    return value


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class CommandChecks(unittest.TestCase):
    def test_model_and_effort_are_pinned(self):
        self.assertEqual((handoff.MODEL, handoff.EFFORT), ("claude-opus-5-5", "max"))
        for mode in ("review", "implement"):
            command = handoff.command_for(args(mode=mode), "/bin/claude", "rules")
            self.assertEqual(option(command, "--model"), "claude-opus-5-5")
            self.assertEqual(option(command, "--effort"), "max")
            self.assertEqual(command.count("--model"), 1)
            self.assertFalse([part for part in command if "fallback" in part])
        for model, effort in [("opus", "max"), ("claude-sonnet-5", "max"),
                              ("claude-opus-5-5", "high"), ("claude-opus-5-5", None)]:
            with self.subTest(model=model, effort=effort), self.assertRaises(ValueError):
                handoff.command_for(args(model=model, effort=effort), "/bin/claude", "rules")

    def test_review_is_read_only(self):
        command = handoff.command_for(args(), "/bin/claude", "rules")
        self.assertEqual(option(command, "--tools"), "Read,Glob,Grep")
        self.assertEqual(option(command, "--allowedTools"), "Read,Glob,Grep")
        self.assertEqual(option(command, "--permission-mode"), "dontAsk")
        self.assertEqual(option(command, "--mcp-config"), '{"mcpServers":{}}')
        for flag in ("--restricted", "--safe-mode", "--strict-mcp-config",
                     "--no-session-persistence", "--disable-slash-commands"):
            self.assertIn(flag, command)
        self.assertIn("Agent", option(command, "--disallowedTools").split(","))
        for unsafe in ("--dangerously-skip-permissions", "bypassPermissions", "--bare"):
            self.assertNotIn(unsafe, " ".join(command))

    def test_implementation_adds_only_edit_and_write(self):
        command = handoff.command_for(args(mode="implement"), "/bin/claude", "rules")
        self.assertEqual(option(command, "--tools"), "Read,Glob,Grep,Edit,Write")
        self.assertNotIn("Bash", option(command, "--allowedTools"))

    def test_shell_needs_exact_commands(self):
        exact = "python3 .ai/test_claude_handoff.py"
        command = handoff.command_for(
            args(mode="implement", allow_bash=[exact]), "/bin/claude", "rules"
        )
        self.assertEqual(option(command, "--tools"), "Read,Glob,Grep,Edit,Write,Bash")
        allowed = option(command, "--allowedTools").split(",")
        self.assertIn("Bash(" + exact + ")", allowed)
        self.assertNotIn("Bash", allowed)
        for pattern in ("pytest *", "git:*", "a,b", "echo $(id)", "ls\nrm -rf x", "", " ls"):
            with self.subTest(pattern=pattern), self.assertRaises(ValueError):
                handoff.command_for(
                    args(mode="implement", allow_bash=[pattern]), "/bin/claude", "rules"
                )
        with self.assertRaises(ValueError):
            handoff.command_for(args(allow_bash=["ls"]), "/bin/claude", "rules")

    def test_child_environment_is_isolated(self):
        parent = {"PATH": "/bin", "ANTHROPIC_API_KEY": "test-only",
                  "ANTHROPIC_MODEL": "claude-sonnet-5", "ANTHROPIC_DEFAULT_OPUS_MODEL": "x",
                  "CLAUDE_CODE_USE_BEDROCK": "1", "CLAUDE_CODE_SUBAGENT_MODEL": "haiku",
                  "MAX_THINKING_TOKENS": "1024", "CLAUDE_CODE_EFFORT_LEVEL": "low"}
        with patch.dict(os.environ, parent, clear=True):
            env = handoff.child_environment()
            self.assertEqual(dict(os.environ), parent)
        for key in parent:
            if key not in ("PATH", "CLAUDE_CODE_EFFORT_LEVEL"):
                self.assertNotIn(key, env)
        self.assertEqual(env["PATH"], "/bin")
        self.assertEqual(env["CLAUDE_CODE_EFFORT_LEVEL"], "max")
        self.assertEqual(env["CODEX_CLAUDE_WORKER"], "1")


class Assessment(unittest.TestCase):
    def test_exact_or_dated_model_is_verified(self):
        for usage in ({"claude-opus-5-5": {}}, {"claude-opus-5-5-20260901": {}},
                      {"claude-opus-5-5": {}, "claude-opus-5-5-20260901": {}}):
            self.assertEqual(handoff.assess(result(modelUsage=usage), 0), ("returned", []))

    def test_misleading_success_is_not_verified(self):
        no_usage = {key: value for key, value in result().items() if key != "modelUsage"}
        cases = [
            ("model_unverified", no_usage),
            ("model_unverified", result(modelUsage=None)),
            ("model_unverified", result(modelUsage={})),
            ("model_unverified", result(modelUsage={"claude-sonnet-5": {}})),
            ("model_unverified", result(modelUsage={"opus": {}})),
            ("model_unverified", result(modelUsage={"claude-opus-5-5-latest": {}})),
            ("model_unverified", result(modelUsage={"claude-opus-5-5": {},
                                                    "claude-haiku-4-5-20251001": {}})),
            ("failed", result(is_error=True)),
            ("failed", result(is_error=None)),
            ("failed", result(subtype="error_max_turns")),
            ("failed", result(subtype="error_max_budget_usd")),
            ("failed", ["not", "an", "object"]),
            ("failed", None),
            ("incomplete", result(permission_denials=[{"tool_name": "Write"}])),
            ("incomplete", result(result="")),
        ]
        for expected, response in cases:
            with self.subTest(expected=expected, response=response):
                status, problems = handoff.assess(response, 0)
                self.assertEqual(status, expected)
                self.assertTrue(problems)
        self.assertEqual(handoff.assess(result(), 1)[0], "failed")
        self.assertEqual(handoff.assess(result(), -15, "timed_out")[0], "timed_out")
        self.assertEqual(handoff.assess(None, -15, "interrupted")[0], "interrupted")


class ProjectCase(unittest.TestCase):
    """A throwaway non-Git ROOT, a scrubbed environment, and no real Claude CLI."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.outside = Path(tempfile.mkdtemp()).resolve()
        for path in (self.root, self.outside):
            self.addCleanup(shutil.rmtree, path)
        (self.root / "CLAUDE.md").write_text("Project rules.\n")
        (self.root / "src").mkdir()
        (self.root / "src" / "model.py").write_text("x = 1\n")
        self.brief = self.outside / "brief.md"
        self.brief.write_text("Do the task.\n")
        environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        for patcher in (patch.object(handoff, "ROOT", self.root),
                        patch.dict(os.environ, environment, clear=True),
                        patch.object(handoff.shutil, "which", return_value=None)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def main(self, *argv):
        """Run the launcher; return (exit code, stdout)."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            try:
                code = handoff.main(list(argv))
            except SystemExit as exit:
                code = exit.code
        return code, output.getvalue()


class Workspaces(ProjectCase):
    def test_cli_accepts_only_the_pinned_model_and_effort(self):
        for flags in (["--model", "opus"], ["--model", "claude-sonnet-5"],
                      ["--model", "claude-opus-5-5-20260901"], ["--effort", "high"]):
            with self.subTest(flags=flags):
                self.assertEqual(self.main("--brief", str(self.brief), "--dry-run", *flags)[0], 2)
        code, output = self.main("--brief", str(self.brief), "--dry-run",
                                 "--model", "claude-opus-5-5", "--effort", "max")
        self.assertEqual(code, 0)
        self.assertIn("--model claude-opus-5-5", output)
        self.assertIn("--effort max", output)

    def test_nested_launch_is_refused(self):
        for marker in ("CODEX_CLAUDE_WORKER", "SPS_CLAUDE_WORKER", "CLAUDECODE"):
            with self.subTest(marker=marker), patch.dict(os.environ, {marker: "1"}):
                with self.assertRaises(ValueError):
                    handoff.child_environment()
                with self.assertRaises(ValueError):
                    self.main("--prepare-workspace", "nested")
                with self.assertRaises(ValueError):
                    self.main("--brief", str(self.brief), "--dry-run")
        self.assertFalse((self.root / "tmp").exists())

    def test_prepare_copies_project_without_excluded_entries(self):
        extras = {
            "config/settings.yaml": "a: 1\n", ".env": "SECRET=1\n",
            "config/.env.local": "SECRET=2\n", ".envrc": "export X=1\n",
            "node_modules/pkg/index.js": "", "src/__pycache__/model.pyc": "",
            ".venv/pyvenv.cfg": "", "lab-env/pyvenv.cfg": "", "lab-env/lib/site.py": "",
            "tmp/workflow-install/base_handoff.py": "",
            "tmp/claude-workspaces/old/workspace/src/model.py": "",
        }
        for name, text in extras.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(text)
        os.symlink(self.root / "src" / "model.py", self.root / "src" / "alias.py")
        os.symlink(self.outside, self.root / "outside-link")
        with patch.object(handoff.subprocess, "run", side_effect=AssertionError("no Git")):
            workspace, manifest_path = handoff.prepare_workspace("job-1")
            second, _ = handoff.prepare_workspace("job-2")
        home = self.root / "tmp" / "claude-workspaces" / "job-1"
        self.assertEqual((workspace, manifest_path), (home / "workspace", home / "manifest.json"))
        copied = sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*")
                        if path.is_file() or path.is_symlink())
        self.assertEqual(copied, ["CLAUDE.md", "config/settings.yaml", "src/model.py"])
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["source_root"], str(self.root))
        self.assertEqual(manifest["workspace"], str(workspace))
        self.assertIsNone(manifest["git"])
        self.assertEqual(manifest["files"], {"CLAUDE.md": sha("Project rules.\n"),
                                             "config/settings.yaml": sha("a: 1\n"),
                                             "src/model.py": sha("x = 1\n")})
        for name in (".env", "config/.env.local", ".envrc", "node_modules", "src/__pycache__",
                     ".venv", "lab-env", "tmp", "src/alias.py", "outside-link"):
            self.assertIn(name, manifest["excluded"])
        self.assertFalse((second / "tmp").exists())  # earlier workspaces are not recopied
        (self.root / ".git").mkdir()
        self.assertIn(".git", handoff.scan(self.root)[1])

    def test_prepare_rejects_unsafe_names_reuse_and_symlinked_location(self):
        for name in ("", ".", "..", "../escape", "a/b", ".hidden", "-flag", "Upper",
                     "x" * 49, "sp ace"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                handoff.prepare_workspace(name)
        self.assertEqual(self.main("--prepare-workspace", "../escape")[0], 2)
        self.assertEqual(self.main("--prepare-workspace", "ok", "--brief", str(self.brief))[0], 2)
        handoff.prepare_workspace("once")
        with self.assertRaises(ValueError):
            handoff.prepare_workspace("once")
        shutil.rmtree(self.root / "tmp")
        os.symlink(self.outside, self.root / "tmp")
        with self.assertRaises(ValueError):
            handoff.prepare_workspace("elsewhere")
        self.assertEqual(list(self.outside.iterdir()), [self.brief])

    def test_implementation_runs_only_in_prepared_copies(self):
        def dry_run(*extra):
            return self.main("--brief", str(self.brief), "--mode", "implement", "--dry-run",
                             *extra)[0]
        self.assertEqual(dry_run(), 2)
        self.assertEqual(dry_run("--workspace", str(self.root)), 2)
        self.assertEqual(dry_run("--workspace", str(self.outside)), 2)
        fake = self.root / "tmp" / "claude-workspaces" / "fake" / "workspace"
        fake.mkdir(parents=True)
        self.assertEqual(dry_run("--workspace", str(fake)), 2)
        for text in ("{not json", "[]", json.dumps(
                {"source_root": "/elsewhere", "workspace": str(fake), "files": {}})):
            with self.subTest(manifest=text):
                (fake.parent / "manifest.json").write_text(text)
                self.assertEqual(dry_run("--workspace", str(fake)), 2)
        workspace, _ = handoff.prepare_workspace("real")
        with patch.object(handoff.subprocess, "run", side_effect=AssertionError("no subprocess")):
            code, output = self.main("--brief", str(self.brief), "--mode", "implement",
                                     "--workspace", str(workspace), "--dry-run")
        self.assertEqual(code, 0)
        metadata = json.JSONDecoder().raw_decode(output)[0]
        self.assertEqual(metadata["workspace"], str(workspace))
        self.assertIsNone(metadata["git"])
        self.assertEqual(self.main("--brief", str(self.brief), "--workspace", str(workspace),
                                   "--dry-run")[0], 2)

    def test_change_summary_reports_hashes_without_touching_root(self):
        workspace, manifest_path = handoff.prepare_workspace("edits")
        (workspace / "src" / "model.py").write_text("x = 2\n")
        (workspace / "src" / "new.py").write_text("y = 1\n")
        (workspace / "CLAUDE.md").unlink()
        (workspace / "src" / "__pycache__").mkdir()
        os.symlink(self.outside, workspace / "escape")
        changes = handoff.workspace_changes(json.loads(manifest_path.read_text()))
        by_path = {item["path"]: item for item in changes["changed"]}
        self.assertEqual(sorted(by_path), ["CLAUDE.md", "src/model.py", "src/new.py"])
        self.assertEqual(by_path["src/model.py"]["prepared_sha256"], sha("x = 1\n"))
        self.assertEqual(by_path["src/model.py"]["workspace_sha256"], sha("x = 2\n"))
        self.assertEqual(by_path["src/model.py"]["root_sha256_now"], sha("x = 1\n"))
        self.assertIsNone(by_path["src/new.py"]["prepared_sha256"])
        self.assertIsNone(by_path["CLAUDE.md"]["workspace_sha256"])
        self.assertEqual(changes["unhashed_new_entries"], ["escape", "src/__pycache__"])
        self.assertEqual((self.root / "src" / "model.py").read_text(), "x = 1\n")

    def test_parent_run_is_provenance_only(self):
        parent = self.root / "tmp" / "claude-handoffs" / "20260924T000000Z-0000abcd"
        parent.mkdir(parents=True)
        (parent / "request.json").write_text(json.dumps(
            {"status": "incomplete", "brief_sha256": "abc", "session_id": "s-1"}))
        code, output = self.main("--brief", str(self.brief), "--parent-run", str(parent),
                                 "--dry-run")
        self.assertEqual(code, 0)
        link = json.JSONDecoder().raw_decode(output)[0]["parent_run"]
        self.assertEqual((link["path"], link["status"], link["session_id"]),
                         (str(parent), "incomplete", "s-1"))
        for text in ("[1, 2]", "{broken"):
            (parent / "request.json").write_text(text)
            self.assertEqual(self.main("--brief", str(self.brief), "--parent-run", str(parent),
                                       "--dry-run")[0], 2)
        self.assertEqual(self.main("--brief", str(self.brief), "--parent-run",
                                   str(self.outside), "--dry-run")[0], 2)


class Runs(ProjectCase):
    def use_fake_cli(self, response, write=None):
        (self.outside / "fake_cli.py").write_text(FAKE_CLI)
        (self.outside / "plan.json").write_text(json.dumps(
            {"response": response, "write": write or {}, "watched_env": WATCHED_ENV}))
        cli = self.outside / "claude"
        cli.write_text("#!/bin/sh\nexec %s %s \"$@\"\n" % (
            shlex.quote(sys.executable), shlex.quote(str(self.outside / "fake_cli.py"))))
        cli.chmod(0o755)
        patcher = patch.object(handoff.shutil, "which", return_value=str(cli))
        patcher.start()
        self.addCleanup(patcher.stop)

    def evidence(self):
        runs = sorted((self.root / "tmp" / "claude-handoffs").iterdir())
        self.assertEqual(len(runs), 1)
        return runs[0], json.loads((runs[0] / "request.json").read_text())

    def run_dir(self):
        path = self.outside / "run"
        path.mkdir()
        (path / "brief.md").write_text("brief\n")
        return path

    def test_verified_implementation_keeps_edits_in_workspace(self):
        workspace, _ = handoff.prepare_workspace("impl")
        self.use_fake_cli(result(), write={"src/model.py": "x = 2\n", "src/new.py": "y = 1\n"})
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-only",
                                     "ANTHROPIC_MODEL": "claude-sonnet-5"}):
            code, output = self.main("--brief", str(self.brief), "--mode", "implement",
                                     "--workspace", str(workspace))
        self.assertEqual(code, 0, output)
        run_dir, request = self.evidence()
        for name in ("brief.md", "request.json", "response.json", "stderr.log", "report.md"):
            self.assertTrue((run_dir / name).is_file(), name)
        self.assertEqual(request["status"], "returned")
        self.assertEqual((request["model_requested"], request["effort_requested"]),
                         ("claude-opus-5-5", "max"))
        self.assertIn("does not report", request["effort_evidence"])
        self.assertEqual(request["models_reported"], ["claude-opus-5-5"])
        self.assertEqual(option(request["command"], "--model"), "claude-opus-5-5")
        self.assertEqual(option(request["command"], "--effort"), "max")
        self.assertEqual([item["path"] for item in request["workspace_changes"]["changed"]],
                         ["src/model.py", "src/new.py"])
        self.assertEqual((self.root / "src" / "model.py").read_text(), "x = 1\n")
        self.assertFalse((self.root / "src" / "new.py").exists())
        self.assertEqual((run_dir / "report.md").read_text(), "done\n")
        seen = json.loads((self.outside / "seen.json").read_text())
        self.assertEqual(seen["stdin"], "Do the task.\n")
        self.assertEqual(seen["cwd"], str(workspace))
        self.assertEqual(seen["env"], {"CODEX_CLAUDE_WORKER": "1",
                                       "CLAUDE_CODE_EFFORT_LEVEL": "max",
                                       "ANTHROPIC_API_KEY": None, "ANTHROPIC_MODEL": None})

    def test_extra_routed_model_is_not_verified(self):
        usage = {"claude-opus-5-5": {}, "claude-haiku-4-5-20251001": {}}
        self.use_fake_cli(result(modelUsage=usage))
        code, _ = self.main("--brief", str(self.brief))
        self.assertEqual(code, 1)
        _, request = self.evidence()
        self.assertEqual(request["status"], "model_unverified")
        self.assertEqual(request["models_reported"], sorted(usage))
        self.assertIn("claude-haiku-4-5-20251001", " ".join(request["problems"]))

    def test_non_object_response_is_failed(self):
        self.use_fake_cli(["not", "an", "object"])
        code, _ = self.main("--brief", str(self.brief))
        self.assertEqual(code, 1)
        run_dir, request = self.evidence()
        self.assertEqual((request["status"], request["models_reported"]), ("failed", []))
        self.assertIn("No text result", (run_dir / "report.md").read_text())

    def test_missing_cli_is_a_clear_error(self):
        self.assertEqual(self.main("--brief", str(self.brief))[0], 1)
        run_dir, request = self.evidence()
        self.assertEqual(request["status"], "failed")
        self.assertIn("not installed", (run_dir / "stderr.log").read_text())

    def test_auth_timeout_keeps_final_evidence(self):
        self.use_fake_cli(result())
        with patch.object(handoff, "check_cli", side_effect=subprocess.TimeoutExpired("auth", 30)):
            code, _ = self.main("--brief", str(self.brief))
        self.assertEqual(code, 1)
        run_dir, request = self.evidence()
        self.assertEqual(request["status"], "timed_out")
        self.assertTrue((run_dir / "report.md").exists())
        self.assertIn("auth", (run_dir / "stderr.log").read_text())

    def test_spawn_failure_never_leaves_running_status(self):
        self.use_fake_cli(result())
        with patch.object(handoff, "check_cli", return_value=("2.1.300", {})), \
                patch.object(handoff.subprocess, "Popen", side_effect=OSError("spawn failed")):
            code, _ = self.main("--brief", str(self.brief))
        self.assertEqual(code, 1)
        run_dir, request = self.evidence()
        self.assertEqual(request["status"], "failed")
        self.assertIn("spawn failed", (run_dir / "stderr.log").read_text())

    def test_termination_during_preflight_finalizes_record(self):
        self.use_fake_cli(result())
        before = signal.getsignal(signal.SIGTERM)
        timer = threading.Timer(0.2, os.kill, (os.getpid(), signal.SIGTERM))
        timer.start()
        self.addCleanup(timer.cancel)
        with patch.object(handoff, "check_cli", side_effect=lambda *a: time.sleep(3)):
            code, _ = self.main("--brief", str(self.brief))
        self.assertEqual(code, 1)
        _, request = self.evidence()
        self.assertEqual(request["status"], "interrupted")
        self.assertEqual(signal.getsignal(signal.SIGTERM), before)

    def test_change_scan_failure_is_incomplete_not_empty_success(self):
        workspace, _ = handoff.prepare_workspace("scan-failure")
        self.use_fake_cli(result())
        with patch.object(handoff, "workspace_changes", side_effect=OSError("scan failed")):
            code, output = self.main("--brief", str(self.brief), "--mode", "implement",
                                     "--workspace", str(workspace))
        self.assertEqual(code, 1)
        _, request = self.evidence()
        self.assertEqual(request["status"], "incomplete")
        self.assertFalse(request["implementation_verified"])
        self.assertIn('"changed_files": null', output)
        self.assertIn('"change_scan_error": "scan failed"', output)

    def test_timeout_kills_descendant_after_leader_exits(self):
        child_pid = self.outside / "child.pid"
        child_code = ("import os,signal,time; from pathlib import Path; "
                      "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                      "Path(%r).write_text(str(os.getpid())); time.sleep(60)" % str(child_pid))
        leader_code = ("import subprocess,sys,time; "
                       "subprocess.Popen([sys.executable, '-c', %r]); time.sleep(60)" % child_code)
        try:
            code, stopped = handoff.run_worker(
                [sys.executable, "-c", leader_code], self.root, dict(os.environ), self.run_dir(), 1)
            self.assertEqual(stopped, "timed_out")
            self.assertIsNotNone(code)
            self.assertTrue(child_pid.exists())
            pid = int(child_pid.read_text())
            deadline = time.monotonic() + 2
            while True:
                state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)],
                                       capture_output=True, text=True).stdout.strip()
                if not state or state.startswith("Z") or time.monotonic() >= deadline:
                    break
                time.sleep(0.05)
            self.assertTrue(not state or state.startswith("Z"), state)
        finally:
            if child_pid.exists():
                try:
                    os.kill(int(child_pid.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_timeout_stops_the_worker(self):
        run_dir = self.run_dir()
        started = time.monotonic()
        code, stopped = handoff.run_worker(SLEEPER, self.root, dict(os.environ), run_dir, 1)
        self.assertEqual(stopped, "timed_out")
        self.assertNotEqual(code, 0)
        self.assertLess(time.monotonic() - started, 15)
        response = handoff.load_json(run_dir / "response.json")
        self.assertEqual(handoff.assess(response, code, stopped)[0], "timed_out")

    def test_termination_signal_stops_the_worker(self):
        if threading.current_thread() is not threading.main_thread():
            self.skipTest("signal handlers need the main thread")
        before = signal.getsignal(signal.SIGTERM)
        timer = threading.Timer(1.0, os.kill, (os.getpid(), signal.SIGTERM))
        timer.start()
        self.addCleanup(timer.cancel)
        code, stopped = handoff.run_worker(SLEEPER, self.root, dict(os.environ),
                                           self.run_dir(), 30)
        self.assertEqual(stopped, "interrupted")
        self.assertNotEqual(code, 0)
        self.assertEqual(signal.getsignal(signal.SIGTERM), before)


if __name__ == "__main__":
    unittest.main()
