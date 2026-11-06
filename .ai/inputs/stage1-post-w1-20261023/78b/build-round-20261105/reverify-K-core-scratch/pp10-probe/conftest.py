"""PP10: the 7-8B kit's tests never reach the network or start a real process (the lead's ruling PP10, after one
development test run in the kit round started a real ``ssh`` to 203.0.113.9 with a fake token: build-K3.md §7 item 2).

The guard below is an autouse fixture over every test in this folder. While a test runs it replaces, at the bottom of
the standard library, the five ways a test could leave the process: ``subprocess.Popen.__init__`` (every
``subprocess.run``, ``check_output``, ``call``, ``Popen`` and ``os.popen`` goes through it, however early the caller
bound ``subprocess.run``, so the K3 incident's path, host.gated_download's default runner, is caught), ``os.system``,
``os.posix_spawn`` / ``os.posix_spawnp``, a socket's ``connect`` / ``connect_ex`` and ``socket.create_connection``,
and ``urllib.request.OpenerDirector.open`` (``urlopen`` and every ``build_opener(...).open``). Each raises
``NetworkOrProcessRefused`` (a RuntimeError) naming the call, so the test fails at once and nothing starts.

A test that must exercise a code path which spawns replaces the call with a fake first (monkeypatch the module's
``subprocess`` / ``urllib`` / ``socket`` name, or pass ``runner=`` / ``run=`` / ``get=`` as the kit's functions take
them): a fake never reaches the guard. A test that needs a real LOCAL process (the kit's own interpreter computing an
engine hash, ``git`` reading HEAD) requests ``local_processes``, which permits exactly these programs by path and
nothing else (never ``ssh``, ``scp``, ``gh``, ``curl``, ``caffeinate``, ``runpodctl``, a bare ``python3``); the network
and ``os.system`` stay refused. The mutation runners (tests/run_mutants_*.py) are plain Python processes, not tests,
and start pytest as usual; inside those pytest runs this guard is active."""
from __future__ import annotations

import os
import pathlib
import socket
import subprocess
import sys
import urllib.request

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]           # the repository root this kit sits in
LOCAL_PROGRAMS = (sys.executable, str(ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"),
                  str(ROOT / ".venv/bin/python"), "git")
NEVER = ("ssh", "scp", "sftp", "gh", "curl", "wget", "caffeinate", "runpodctl", "rsync", "nc", "python3")


class NetworkOrProcessRefused(RuntimeError):
    """PP10: a test reached a real subprocess start, os.system, socket connect or urllib open."""


def _refuse(what: str, detail: str) -> None:
    raise NetworkOrProcessRefused(
        f"PP10: the kit's tests never start a real {what} ({detail}); replace it with a fake (monkeypatch the module's "
        "subprocess, urllib or socket name, or pass the function's runner= / run= / get=), or request the "
        "local_processes fixture for the kit's own interpreter or git")


def _program(args) -> str:
    if isinstance(args, (str, bytes, os.PathLike)):
        argv = [args]
    else:
        try:
            argv = list(args)
        except TypeError:
            argv = [args]
    return os.fsdecode(argv[0]) if argv else ""


@pytest.fixture(autouse=True)
def pp10_guard(monkeypatch):
    """Refuse every real process start and network connection during the test (PP10). Yields the allow-list that
    ``local_processes`` extends."""
    allowed: list[str] = []
    real_init = subprocess.Popen.__init__

    def guarded_init(self, args, *a, **kw):
        prog = _program(args)
        base = os.path.basename(prog)
        if prog in allowed and base not in NEVER:
            return real_init(self, args, *a, **kw)
        _refuse("subprocess", f"argv[0] = {prog!r}")

    monkeypatch.setattr(subprocess.Popen, "__init__", guarded_init)
    monkeypatch.setattr(os, "system", lambda command: _refuse("os.system", repr(command)[:80]))
    for name in ("posix_spawn", "posix_spawnp"):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, lambda path, *a, **kw: _refuse(name, repr(path)[:80]))
    monkeypatch.setattr(socket.socket, "connect", lambda self, address: _refuse("socket connect", repr(address)[:80]))
    monkeypatch.setattr(socket.socket, "connect_ex", lambda self, address: _refuse("socket connect_ex", repr(address)[:80]))
    monkeypatch.setattr(socket, "create_connection", lambda address, *a, **kw: _refuse("socket connection", repr(address)[:80]))
    monkeypatch.setattr(urllib.request.OpenerDirector, "open",
                        lambda self, fullurl, *a, **kw: _refuse("urllib open", repr(getattr(fullurl, "full_url", fullurl))[:80]))
    yield allowed


@pytest.fixture
def local_processes(pp10_guard):
    """Permit the kit's own interpreter(s) and git, by path, for this test only (a real local process; no network)."""
    pp10_guard.extend(LOCAL_PROGRAMS)
    return tuple(LOCAL_PROGRAMS)
