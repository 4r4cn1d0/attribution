#!/usr/bin/env python3
"""Run one bounded Claude assignment for the Codex lead and preserve its evidence.

Review runs read ROOT with Read/Glob/Grep only. Implementation runs edit only a
copy made by --prepare-workspace NAME; nothing is applied to ROOT automatically.
"""

import argparse
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
# Pinned by the user: exactly Claude Opus 5.5 at max effort. There is no alias,
# fallback model or effort choice; change these only on an explicit user request.
MODEL = "claude-opus-5-5"
EFFORT = "max"
WORKER_RULES = """You are a bounded worker reporting to the initiating Codex task.
Follow the assignment and the project instructions below. You are not alone in
the codebase: preserve others' changes and touch only your assigned files.
Do not invoke Claude, Codex, subagents, MCP agents, or any recursive review loop.
Do not commit, push, publish, or launch experiments unless the brief explicitly
authorizes that action. Return blockers instead of silently changing the spec.
Return changed files, commands and exit status, evidence paths, acceptance checks,
and unresolved issues. Do not claim a check passed unless you ran it.
"""
WORKSPACE_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,47}")
# Never copied into a prepared workspace, matched by name at any depth. Also
# skipped: .env and .env.* files, symlinks, and pyvenv.cfg/conda-meta environments.
EXCLUDED_NAMES = {
    ".git", "tmp", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".cache", ".ipynb_checkpoints", ".hypothesis", ".tox", ".nox",
    ".venv", "venv", ".conda", ".envrc", ".DS_Store",
}
# Most severe first. "returned" checks transport/routing, never implementation correctness.
UNVERIFIED = ("timed_out", "interrupted", "failed", "model_unverified", "incomplete")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def load_json(path):
    """Parsed JSON, or None when the file is missing or is not valid JSON."""
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def git_state(path):
    """Optional provenance: None unless path is itself a Git checkout and Git runs."""
    if not (path / ".git").exists():
        return None
    state = {}
    try:
        for key, args in (("head", ["rev-parse", "HEAD"]), ("status", ["status", "--short"])):
            state[key] = subprocess.run(
                ["git", "-C", str(path), *args], capture_output=True, text=True,
                timeout=30, check=True,
            ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return state


def child_environment():
    """Environment for the worker only; refuses to run inside a delegated worker."""
    if any(os.environ.get(key) for key in (
        "CODEX_CLAUDE_WORKER", "SPS_CLAUDE_WORKER", "CLAUDECODE"
    )):
        raise ValueError("A delegated worker may not launch another agent.")
    env = os.environ.copy()
    # Affect only this child. Do not mutate the user's shell or credential files.
    # ANTHROPIC_* also covers model overrides such as ANTHROPIC_MODEL.
    for key in list(env):
        if key.startswith("ANTHROPIC_") or key in (
            "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX",
            "CLAUDE_CODE_USE_FOUNDRY", "CLAUDE_CODE_SIMPLE",
            "CLAUDE_CODE_SUBAGENT_MODEL", "MAX_THINKING_TOKENS",
        ):
            env.pop(key)
    env["CODEX_CLAUDE_WORKER"] = "1"
    env["CLAUDE_CODE_EFFORT_LEVEL"] = EFFORT
    return env


def bash_rule(command):
    """Permission rule for one exact command; wildcards and rule separators are refused."""
    if not command.strip() or command != command.strip() or re.search(r"[*,()\r\n]", command):
        raise ValueError(
            "--allow-bash takes one exact command without *, commas, parentheses "
            "or newlines: " + repr(command)
        )
    return "Bash(" + command + ")"


def command_for(args, cli, instructions):
    """Review: Read/Glob/Grep. Implement: adds Edit/Write. Bash only for exact commands."""
    if args.model != MODEL or args.effort != EFFORT:
        raise ValueError("Only %s at %s effort is allowed (see MODEL/EFFORT)." % (MODEL, EFFORT))
    if args.mode == "review" and args.allow_bash:
        raise ValueError("Review runs have no shell; Codex runs checks separately.")
    names = ["Read", "Glob", "Grep"]
    if args.mode == "implement":
        names += ["Edit", "Write"]
    allowed = names.copy()
    if args.allow_bash:
        names += ["Bash"]
        allowed += [bash_rule(command) for command in args.allow_bash]
    return [
        cli, "--print", "--model", MODEL,
        "--output-format", "json", "--max-turns", str(args.max_turns),
        "--restricted", "--safe-mode", "--setting-sources", "",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--tools", ",".join(names), "--allowedTools", ",".join(allowed),
        "--disallowedTools", "Agent,Task,mcp__*,Bash(claude *),Bash(codex *)",
        "--permission-mode", "dontAsk", "--permission-prompts", "none",
        "--no-session-persistence", "--no-chrome", "--disable-slash-commands",
        "--append-system-prompt", instructions, "--effort", EFFORT,
    ]


def scan(top):
    """Relative POSIX paths of regular files to copy, and of entries left out."""
    files, skipped = [], []
    pending = [top]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(top).as_posix()
                if (entry.is_symlink() or entry.name in EXCLUDED_NAMES
                        or entry.name == ".env" or entry.name.startswith(".env.")):
                    skipped.append(relative)
                elif entry.is_dir(follow_symlinks=False):
                    if (path / "pyvenv.cfg").exists() or (path / "conda-meta").exists():
                        skipped.append(relative)
                    else:
                        pending.append(path)
                elif entry.is_file(follow_symlinks=False):
                    files.append(relative)
                else:  # sockets, FIFOs, devices
                    skipped.append(relative)
    return sorted(files), sorted(skipped)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_workspace(name):
    """Copy ROOT to a new ROOT/tmp/claude-workspaces/NAME/workspace.

    The manifest beside (not inside) the copy records the source root and the
    hash of every copied file. It is audit metadata, not a security boundary.
    """
    if not WORKSPACE_NAME.fullmatch(name):
        raise ValueError(
            "Workspace NAME needs 1-48 of a-z, 0-9, '-', '_', starting with a letter or digit."
        )
    home = ROOT / "tmp" / "claude-workspaces" / name
    for directory in (home.parent.parent, home.parent):
        if directory.is_symlink():
            raise ValueError("Refusing symlinked workspace location: " + str(directory))
        directory.mkdir(exist_ok=True)
    try:
        home.mkdir(mode=0o700)
    except FileExistsError:
        raise ValueError("Workspace already exists; choose a new NAME: " + str(home)) from None
    workspace = home / "workspace"
    workspace.mkdir()
    files, skipped = scan(ROOT)  # tmp is skipped, so earlier workspaces are never copied
    hashes = {}
    for relative in files:
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target, follow_symlinks=False)
        hashes[relative] = sha256_file(target)
    write_json(home / "manifest.json", {
        "name": name, "source_root": str(ROOT), "workspace": str(workspace),
        "created": now(), "git": git_state(ROOT), "files": hashes, "excluded": skipped,
    })
    return workspace, home / "manifest.json"


def prepared_manifest(path):
    """Manifest showing path is a prepared copy of this ROOT; ROOT itself never qualifies."""
    workspace = Path(path).resolve()
    home = workspace.parent
    if (workspace == ROOT or workspace.name != "workspace" or not workspace.is_dir()
            or home.parent != ROOT / "tmp" / "claude-workspaces"
            or not WORKSPACE_NAME.fullmatch(home.name)):
        raise ValueError("Implementation runs only in a copy made by --prepare-workspace, never in ROOT.")
    manifest = load_json(home / "manifest.json")
    if (home / "manifest.json").is_symlink() or not isinstance(manifest, dict):
        raise ValueError("Missing or invalid workspace manifest: " + str(home / "manifest.json"))
    if (manifest.get("source_root") != str(ROOT) or manifest.get("workspace") != str(workspace)
            or not isinstance(manifest.get("files"), dict)):
        raise ValueError("The workspace manifest does not describe a copy of this project.")
    return manifest


def workspace_changes(manifest):
    """Changed-file hash summary against the prepared copy; nothing is applied to ROOT."""
    workspace = Path(manifest["workspace"])
    prepared = manifest["files"]
    files, unhashed = scan(workspace)
    current = {relative: sha256_file(workspace / relative) for relative in files}
    changed = []
    for relative in sorted(set(prepared) | set(current)):
        if prepared.get(relative) != current.get(relative):
            source = ROOT / relative
            changed.append({
                "path": relative, "prepared_sha256": prepared.get(relative),
                "workspace_sha256": current.get(relative),
                # Differs from prepared_sha256 when ROOT itself changed after the copy.
                "root_sha256_now": sha256_file(source)
                if source.is_file() and not source.is_symlink() else None,
            })
    # A fresh copy holds no excluded entries, so any listed here were created later.
    return {"changed": changed, "unhashed_new_entries": unhashed}


def parent_record(path):
    """Provenance link only: no session is resumed, so the brief must restate context."""
    run_dir = Path(path).resolve()
    request = load_json(run_dir / "request.json")
    if run_dir.parent != ROOT / "tmp" / "claude-handoffs" or not isinstance(request, dict):
        raise ValueError(
            "--parent-run must be a tmp/claude-handoffs run with a JSON-object request.json."
        )
    return {
        "path": str(run_dir), "status": request.get("status"),
        "brief_sha256": request.get("brief_sha256"), "session_id": request.get("session_id"),
    }


def worker_instructions(mode, workspace):
    text = WORKER_RULES + "\nProject instructions:\n" + (ROOT / "CLAUDE.md").read_text()
    if mode == "review":
        return text + "\nThis assignment is read-only. Return your report in the response.\n"
    return text + (
        "\nYou are editing an isolated copy of the project at " + str(workspace) + ".\n"
        "Change files only inside it; the lead inspects and applies changes.\n"
    )


def check_cli(cli, env, cwd):
    """Require Claude Code >= 2.1.280 logged in through the Claude subscription."""
    version = subprocess.check_output(
        [cli, "--version"], text=True, env=env, timeout=30, stderr=subprocess.DEVNULL
    ).strip()
    numbers = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
    if not numbers or tuple(map(int, numbers.groups())) < (2, 1, 280):
        raise ValueError("Update Claude Code with `claude update` (minimum 2.1.280).")
    auth_run = subprocess.run(
        [cli, "--setting-sources", "", "auth", "status", "--json"],
        cwd=cwd, env=env, capture_output=True, text=True, timeout=30,
    )
    try:
        auth = json.loads(auth_run.stdout)
    except ValueError:
        auth = None
    if not isinstance(auth, dict):
        raise ValueError("Cannot verify Claude login. Run `claude auth login --claudeai`.")
    if not auth.get("loggedIn") or auth.get("authMethod") not in ("claude.ai", "oauth"):
        raise ValueError("Subscription login required: run `claude auth login --claudeai`.")
    if auth.get("apiProvider") != "firstParty":
        raise ValueError("The active provider is not the Claude subscription provider.")
    return version, auth


@contextlib.contextmanager
def interrupt_on_termination():
    """Treat SIGTERM/SIGHUP like Ctrl-C so a stopped launcher still stops its worker."""
    def interrupt(signum, frame):
        raise KeyboardInterrupt
    previous = {}
    try:
        for number in (signal.SIGTERM, signal.SIGHUP):
            if signal.getsignal(number) is not signal.SIG_IGN:  # respect nohup
                previous[number] = signal.signal(number, interrupt)
    except ValueError:  # only the main thread may install handlers
        pass
    try:
        yield
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def stop_process(process):
    """Stop the worker's whole process group: SIGTERM, then SIGKILL after 5 seconds."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait()
        return
    # Do not reap the leader until group cleanup: descendants may outlive it.
    # A fixed grace also avoids killpg(..., 0)'s EPERM for zombie-only groups on macOS.
    time.sleep(5)
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        # macOS may return EPERM when the unreaped leader is already dead and no
        # signalable group members remain. A live leader is an actual cleanup failure.
        if process.poll() is None:
            raise
    process.wait()


def run_worker(command, cwd, env, run_dir, timeout):
    """Run once, never retried, with brief.md on stdin; return (exit code, stop reason)."""
    stopped = None
    with interrupt_on_termination(), (run_dir / "brief.md").open("rb") as brief:
        with (run_dir / "response.json").open("wb") as output, \
                (run_dir / "stderr.log").open("wb") as error:
            process = subprocess.Popen(
                command, cwd=cwd, env=env, stdin=brief, stdout=output, stderr=error,
                start_new_session=True,
            )
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                stopped = "timed_out"
            except KeyboardInterrupt:
                stopped = "interrupted"
            if stopped:
                stop_process(process)
    return process.returncode, stopped


def accepted_model(name):
    """The pinned ID or its dated snapshot, e.g. claude-opus-5-5-20260901."""
    return name == MODEL or re.fullmatch(re.escape(MODEL) + r"-\d{8}", name) is not None


def assess(result, returncode, stopped=None):
    """Return (status, problems); "returned" means a clean response from MODEL.

    Effort is not judged: the CLI result does not report the effective effort.
    The GPT lead must separately verify artifacts and acceptance criteria.
    """
    found = []
    if stopped:
        found.append((stopped, "stopped by the launcher: " + stopped))
    if returncode != 0:
        found.append(("failed", "exit code %s" % returncode))
    if not isinstance(result, dict):
        found.append(("failed", "response is not a JSON object"))
    else:
        if result.get("is_error") is not False:
            found.append(("failed", "is_error=%r" % result.get("is_error")))
        if result.get("subtype") != "success":
            found.append(("failed", "subtype=%r" % result.get("subtype")))
        usage = result.get("modelUsage")
        if not isinstance(usage, dict) or not usage:
            found.append(("model_unverified", "no model identity in modelUsage"))
        else:
            others = sorted(name for name in usage if not accepted_model(name))
            if others:
                found.append(("model_unverified", "unrequested models: " + ", ".join(others)))
        if result.get("permission_denials"):
            found.append(("incomplete", "permission denials; see request.json"))
        if not str(result.get("result") or "").strip():
            found.append(("incomplete", "empty result text"))
    if not found:
        return "returned", []
    status = min((status for status, _ in found), key=UNVERIFIED.index)
    return status, [problem for _, problem in found]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument("--brief", type=Path, help="Assignment for one worker run")
    task.add_argument("--prepare-workspace", metavar="NAME",
                      help="Copy the project for implementation runs, then exit")
    parser.add_argument("--model", default=MODEL, choices=(MODEL,), help="Pinned; see MODEL")
    parser.add_argument("--effort", default=EFFORT, choices=(EFFORT,), help="Pinned; see EFFORT")
    parser.add_argument("--mode", choices=("review", "implement"), default="review")
    parser.add_argument("--workspace", type=Path, help="Prepared copy (implement mode only)")
    parser.add_argument("--allow-bash", action="append", default=[], metavar="EXACT_COMMAND")
    parser.add_argument("--parent-run", type=Path, help="Earlier handoff directory (provenance)")
    parser.add_argument("--max-turns", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=1800, help="Seconds")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    env = child_environment()
    if args.prepare_workspace is not None:
        if (args.workspace or args.allow_bash or args.parent_run or args.dry_run
                or args.mode != "review"):
            parser.error("--prepare-workspace takes only a NAME.")
        try:
            workspace, manifest_path = prepare_workspace(args.prepare_workspace)
        except ValueError as error:
            parser.error(str(error))
        print(json.dumps({"workspace": str(workspace), "manifest": str(manifest_path)}, indent=2))
        return 0
    if args.max_turns < 1 or args.timeout < 1:
        parser.error("Turn and time limits must be positive.")
    if args.mode == "review" and args.workspace:
        parser.error("Review runs read ROOT; --workspace is for implementation only.")
    manifest = None
    if args.mode == "implement":
        try:
            manifest = prepared_manifest(args.workspace or ROOT)
        except ValueError as error:
            parser.error(str(error))
    workspace = Path(manifest["workspace"]) if manifest else ROOT
    try:
        brief = args.brief.resolve().read_text(encoding="utf-8")
    except (OSError, ValueError) as error:
        parser.error("Cannot read the brief: " + str(error))
    if not brief.strip():
        parser.error("The brief is empty.")
    parent = None
    if args.parent_run:
        try:
            parent = parent_record(args.parent_run)
        except ValueError as error:
            parser.error(str(error))
    if not (ROOT / "CLAUDE.md").is_file():
        parser.error("Project instructions are missing: " + str(ROOT / "CLAUDE.md"))
    cli = shutil.which("claude")
    try:
        command = command_for(args, cli or "claude", worker_instructions(args.mode, workspace))
    except ValueError as error:
        parser.error(str(error))
    metadata = {
        "mode": args.mode, "workspace": str(workspace),
        "manifest": str(workspace.parent / "manifest.json") if manifest else None,
        "brief_path": str(args.brief.resolve()),
        "brief_sha256": hashlib.sha256(brief.encode()).hexdigest(),
        "model_requested": MODEL, "effort_requested": EFFORT,
        "effort_evidence": "requested via --effort and CLAUDE_CODE_EFFORT_LEVEL; "
                           "the CLI result does not report the effective effort",
        "allowed_bash": args.allow_bash, "max_turns": args.max_turns,
        "timeout_seconds": args.timeout, "parent_run": parent, "git": git_state(ROOT),
    }
    if args.dry_run:
        preview = command.copy()
        preview[preview.index("--append-system-prompt") + 1] = "<worker rules + current CLAUDE.md>"
        print(json.dumps(metadata, indent=2))
        print(shlex.join(preview))
        return 0
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = ROOT / "tmp" / "claude-handoffs" / (stamp + "-" + uuid.uuid4().hex[:8])
    run_dir.mkdir(parents=True, mode=0o700)
    metadata.update({
        "command": command, "started": now(), "status": "preflight",
        "implementation_verified": False,
    })
    (run_dir / "brief.md").write_text(brief, encoding="utf-8")
    for name in ("response.json", "stderr.log"):
        (run_dir / name).touch()
    write_json(run_dir / "request.json", metadata)
    print("Handoff evidence: " + str(run_dir), flush=True)
    returncode, stopped, execution_error = None, None, None
    try:
        with interrupt_on_termination():
            if not cli:
                raise ValueError("Claude Code is not installed.")
            version, auth = check_cli(cli, env, workspace)
            metadata.update({"cli_version": version, "auth_method": auth.get("authMethod"),
                             "api_provider": auth.get("apiProvider"), "status": "running"})
            write_json(run_dir / "request.json", metadata)
            returncode, stopped = run_worker(command, workspace, env, run_dir, args.timeout)
    except subprocess.TimeoutExpired as error:
        stopped, execution_error = "timed_out", str(error)
    except KeyboardInterrupt:
        stopped, execution_error = "interrupted", "Interrupted during preflight or startup."
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        execution_error = str(error)
    result = load_json(run_dir / "response.json")
    status, problems = assess(result, returncode, stopped)
    if execution_error:
        problems.append(execution_error)
        with (run_dir / "stderr.log").open("a") as handle:
            handle.write("Launcher: " + execution_error + "\n")
    result = result if isinstance(result, dict) else {}
    usage = result.get("modelUsage")
    metadata.update({
        "finished": now(), "exit_code": returncode, "status": status, "problems": problems,
        "subtype": result.get("subtype"), "is_error": result.get("is_error"),
        "num_turns": result.get("num_turns"), "session_id": result.get("session_id"),
        "model_usage": usage,
        "models_reported": sorted(usage) if isinstance(usage, dict) else [],
        "permission_denials": result.get("permission_denials", []),
    })
    if manifest:
        try:
            metadata["workspace_changes"] = workspace_changes(manifest)
        except OSError as error:
            metadata["workspace_changes"] = {"error": str(error)}
            metadata["problems"].append("Cannot enumerate workspace changes: " + str(error))
            if status == "returned":
                status = metadata["status"] = "incomplete"
    write_json(run_dir / "request.json", metadata)
    report = result.get("result") or "No text result; inspect response.json and stderr.log."
    (run_dir / "report.md").write_text(str(report) + "\n")
    summary = {key: metadata[key] for key in ("status", "problems", "exit_code", "models_reported")}
    if manifest:
        change_info = metadata["workspace_changes"]
        summary["changed_files"] = ([item["path"] for item in change_info["changed"]]
                                    if "changed" in change_info else None)
        if "error" in change_info:
            summary["change_scan_error"] = change_info["error"]
        summary["note"] = "Edits stay in the workspace; nothing was applied to ROOT."
    print(json.dumps(summary, indent=2))
    print("Report: " + str(run_dir / "report.md"))
    return 0 if status == "returned" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print("Handoff failed: " + str(error), file=sys.stderr)
        sys.exit(1)
