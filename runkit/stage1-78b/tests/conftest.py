"""PP10: the 7-8B kit's tests never reach the network or start a real process (the lead's ruling PP10, after one
development test run in the kit round started a real ``ssh`` to 203.0.113.9 with a fake token: build-K3.md §7 item 2).

Two layers guard every test in this folder.

1. The process-wide layer (K4a; the core re-verifier's DK-1), installed when pytest imports this file, before any
test module is collected, and never removed. A CPython audit hook (``sys.addaudithook``) refuses, in every phase of
the run (collection, module- and session-scoped fixtures, the tests, C-level calls such as ``_socket.socket.connect``):
``subprocess.Popen`` unless its EXECUTABLE (the ``executable=`` argument, else argv[0]) is one of the programs the
``local_processes`` fixture has put in ALLOWED for the running test (the flag; empty otherwise); ``os.system``;
``os.exec*``; ``os.posix_spawn`` / ``os.posix_spawnp``; ``os.spawn*``; ``os.fork`` / ``os.forkpty``; a socket's
``connect`` / ``connect_ex`` / ``sendto`` / ``sendmsg`` to anything but a loopback address or a unix socket; the name
lookups ``getaddrinfo`` / ``gethostbyname`` / ``gethostbyname_ex`` / ``gethostbyaddr`` / ``getnameinfo`` of anything
but a loopback name or address (or None); every ``urllib`` open; ``http.client``'s connect to a non-loopback host.
Two gaps of the audit events are closed beside it: multiprocessing's spawn and forkserver start their child through
``_posixsubprocess.fork_exec``, which raises no event, so that name is replaced by a refusal (subprocess keeps its own
reference, bound at its import, behind the audited ``subprocess.Popen``); and CPython resolves a host NAME given to a
socket's ``connect`` / ``sendto`` / ``sendmsg`` before it raises the event (M: an address it cannot parse fails with
no event), so ``socket.socket``'s four methods are wrapped process-wide to refuse a non-loopback address before the
C call. Not covered: ctypes or another C extension calling the system directly; a direct call of subprocess's private
``_fork_exec``; a host name given to a bare ``_socket.socket`` (one DNS query could leave before the hook refuses the
connect). No kit file or test does any of these.

2. The per-test fixture (``pp10_guard``, autouse; PP10's first form, kept): while a test runs it replaces the same
calls at the Python level, so a test fails at once with a message naming the call (``subprocess (argv[0] = ...)``,
``socket connect``, ``urllib open``, ``name lookup socket.<name>``, ...): ``subprocess.Popen.__init__`` (argv[0] and
the ``executable=`` argument; every ``subprocess.run``, ``check_output``, ``call``, ``Popen`` and ``os.popen`` goes
through it, however early the caller bound ``subprocess.run``, so the K3 incident's path, host.gated_download's
default runner, is caught), ``os.system``, ``os.posix_spawn`` / ``os.posix_spawnp``, ``os.fork`` / ``os.forkpty`` /
``os.execv`` / ``os.execve`` (os.spawn*, os.exec* and pty.fork go through them), a socket's ``connect`` /
``connect_ex`` and ``socket.create_connection``, the name lookups (with ``getnameinfo``; loopback names and None stay
local and pass), a socket's ``sendto`` / ``sendmsg`` on an internet socket (IPv4 and IPv6), and
``urllib.request.OpenerDirector.open``. Each refusal of either layer raises ``NetworkOrProcessRefused`` (a
RuntimeError); the process-wide layer's message starts "PP10 (process-wide audit hook)".

A test that must exercise a code path which spawns replaces the call with a fake first (monkeypatch the module's
``subprocess`` / ``urllib`` / ``socket`` name, or pass ``runner=`` / ``run=`` / ``get=`` as the kit's functions take
them): a fake never reaches either layer. A test that needs a real LOCAL process (the kit's own interpreter computing an
engine hash, ``git`` reading HEAD) requests ``local_processes``, which permits exactly these programs by exact path (or
the bare name ``git``) and nothing else (never ``ssh``, ``scp``, ``gh``, ``curl``, ``caffeinate``, ``runpodctl``, a
bare ``python3``, a shell, nor a file of an allowed program's base name elsewhere), for that test only; the network,
``os.system`` and multiprocessing stay refused. The children of those programs are outside this process and outside
both layers. The mutation runners (tests/run_mutants_*.py) are plain Python processes, not tests, and start pytest as
usual; inside those pytest runs both layers are active."""
from __future__ import annotations

import _posixsubprocess
import _socket
import collections
import ipaddress
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
LOOPBACK = ("localhost", "127.0.0.1", "::1", b"localhost", b"127.0.0.1", b"::1")   # name lookups that send no packet
HOOK_PREFIX = "PP10 (process-wide audit hook): "


class NetworkOrProcessRefused(RuntimeError):
    """PP10: a test reached a real subprocess start, os.system, socket connect or urllib open."""


def _refuse(what: str, detail: str) -> None:
    raise NetworkOrProcessRefused(
        f"PP10: the kit's tests never start a real {what} ({detail}); replace it with a fake (monkeypatch the module's "
        "subprocess, urllib or socket name, or pass the function's runner= / run= / get=), or request the "
        "local_processes fixture for the kit's own interpreter or git")


def _refuse_hook(what: str, detail: str) -> None:
    raise NetworkOrProcessRefused(
        f"{HOOK_PREFIX}the kit's tests never start a real {what} ({detail}), at collection, in any fixture or in a "
        "test; replace it with a fake, or request local_processes for the kit's own interpreter or git")


def _program(args) -> str:
    if isinstance(args, (str, bytes, os.PathLike)):
        argv = [args]
    else:
        try:
            argv = list(args)
        except TypeError:
            argv = [args]
    return os.fsdecode(argv[0]) if argv else ""


# ===== 1. the process-wide layer (DK-1) =============================================================================
# One state per process, kept on the sys module, so a second import of this file (under another module name) shares
# the flag and installs nothing twice (an audit hook cannot be removed).
_STATE = sys.__dict__.setdefault("_pp10_stage1_78b_guard", {"allowed": [], "seen": collections.deque(maxlen=200),
                                                             "installed": False})
ALLOWED: list[str] = _STATE["allowed"]     # the flag: the programs local_processes permits for the running test only
SEEN = _STATE["seen"]                      # the audited events the hook let through (event, detail): the tests' check
                                           # that a real call reaches it


def loopback_host(host) -> bool:
    """True for a name or address that sends no packet off this machine: "localhost" or a loopback IP (127/8, ::1)."""
    if isinstance(host, bytes):
        host = host.decode("ascii", "replace")
    if not isinstance(host, str) or not host:
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.split("%", 1)[0]).is_loopback
    except ValueError:
        return False


def address_refusal(family, address) -> str | None:
    """None when a socket call to ``address`` stays on this machine (no address, a unix socket, a loopback host),
    else a short description of the address for the refusal."""
    if address is None or family == getattr(socket, "AF_UNIX", object()):
        return None
    if family in (socket.AF_INET, socket.AF_INET6) and isinstance(address, tuple) and address \
            and loopback_host(address[0]):
        return None
    return repr(address)[:80]


def program_allowed(program) -> bool:
    """The process-wide check of a program about to start: exactly a path (or bare name) in ALLOWED, never NEVER's."""
    try:
        prog = os.fsdecode(program)
    except TypeError:
        return False
    return prog in ALLOWED and os.path.basename(prog) not in NEVER


def _audit(event: str, args: tuple) -> None:
    if event not in _AUDITED:
        return
    kind = _AUDITED[event]
    if kind == "process":
        if event == "subprocess.Popen":
            if program_allowed(args[0]):
                SEEN.append((event, os.fsdecode(args[0])))
                return
            _refuse_hook("subprocess", f"executable = {args[0]!r}"[:120])
        _refuse_hook(event, repr(args[0])[:80] if args else "no arguments")
    if kind == "socket":
        sock, address = (args + (None, None))[:2]
        detail = address_refusal(getattr(sock, "family", None), address)
        if detail is not None:
            _refuse_hook(event, detail)
    elif kind == "lookup":
        host = args[0] if args else None
        if event == "socket.getnameinfo":
            host = host[0] if isinstance(host, tuple) and host else ""
        if not (host is None and event == "socket.getaddrinfo") and not loopback_host(host):
            _refuse_hook(f"name lookup {event}", repr(host)[:80])
    elif kind == "http":
        host = args[1] if len(args) > 1 else None
        if not loopback_host(host):
            _refuse_hook(event, repr(host)[:80])
    elif kind == "urllib":
        _refuse_hook("urllib open", repr(args[0] if args else None)[:80])
    SEEN.append((event, repr(args[1:2] if kind == "socket" else args[:1])[:80]))


_AUDITED = {"subprocess.Popen": "process", "os.system": "process", "os.exec": "process", "os.posix_spawn": "process",
            "os.spawn": "process", "os.fork": "process", "os.forkpty": "process",
            "socket.connect": "socket", "socket.sendto": "socket", "socket.sendmsg": "socket",
            "socket.getaddrinfo": "lookup", "socket.gethostbyname": "lookup", "socket.gethostbyaddr": "lookup",
            "socket.getnameinfo": "lookup", "urllib.Request": "urllib", "http.client.connect": "http"}


def _fork_exec_refused(*args, **kwargs):
    """multiprocessing's spawn / forkserver start (util.spawnv_passfds) calls _posixsubprocess.fork_exec by name and
    raises no audit event; subprocess holds its own reference (bound at its import) behind subprocess.Popen's event."""
    argv = args[0] if args else None
    _refuse_hook("process through _posixsubprocess.fork_exec (multiprocessing's spawn)", repr(argv)[:80])


def _checked_socket_method(name: str, real):
    """A socket.socket method that refuses a non-loopback address BEFORE the C call (which would resolve a host name,
    sending a DNS query, before its audit event)."""
    def call(self, *args, **kwargs):
        if name in ("connect", "connect_ex"):
            address = args[0] if args else kwargs.get("address")
        elif name == "sendto":
            address = args[-1] if len(args) >= 2 else None
        else:                                                   # sendmsg(buffers[, ancdata[, flags[, address]]])
            address = args[3] if len(args) >= 4 else None
        detail = address_refusal(self.family, address)
        if detail is not None:
            _refuse_hook(f"socket {name} (before any name resolution)", detail)
        return real(self, *args, **kwargs)
    call.__name__ = name
    call.pp10_process_wide = True
    return call


def install() -> None:
    if _STATE["installed"]:
        return
    sys.addaudithook(_audit)
    _posixsubprocess.fork_exec = _fork_exec_refused
    for name in ("connect", "connect_ex", "sendto", "sendmsg"):
        setattr(socket.socket, name, _checked_socket_method(name, getattr(_socket.socket, name)))
    _STATE["installed"] = True


install()


# ===== 2. the per-test fixture (PP10's first form) ==================================================================
@pytest.fixture(autouse=True)
def pp10_guard(monkeypatch):
    """Refuse every real process start and network connection during the test (PP10). Yields ALLOWED, which
    ``local_processes`` extends for this test; it is emptied when the test ends."""
    allowed = ALLOWED
    real_init = subprocess.Popen.__init__

    def guarded_init(self, args, *a, **kw):
        prog = _program(args)
        executable = kw.get("executable", a[1] if len(a) >= 2 else None)    # Popen(args, bufsize, executable, ...)
        programs = [prog] + ([os.fsdecode(executable)] if executable is not None else [])
        if all(p in allowed and os.path.basename(p) not in NEVER for p in programs):
            return real_init(self, args, *a, **kw)
        _refuse("subprocess", f"argv[0] = {prog!r}" + (f", executable = {executable!r}" if executable is not None else ""))

    monkeypatch.setattr(subprocess.Popen, "__init__", guarded_init)
    monkeypatch.setattr(os, "system", lambda command: _refuse("os.system", repr(command)[:80]))
    for name in ("posix_spawn", "posix_spawnp"):
        if hasattr(os, name):          # the name bound per function (fix-K-gated G4: a late-bound name said posix_spawnp)
            monkeypatch.setattr(os, name, lambda path, *a, _name=name, **kw: _refuse(_name, repr(path)[:80]))
    # fix-K-gated G3: a fork or an exec leaves the guarded process (os.spawn* and pty.fork go through these)
    for name in ("fork", "forkpty", "execv", "execve"):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, lambda *a, _name=name, **kw: _refuse(f"os.{_name}", repr(a[:1])[:80]))
    # fix-K-gated G1: a name lookup sends a DNS query before any connect; loopback names only (no packet leaves)
    real_getaddrinfo = socket.getaddrinfo              # the stdlib wrapper; it calls _socket.getaddrinfo at the call
    for name in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):

        def lookup(host, *a, _name=name, **kw):
            if host is None or host in LOOPBACK:       # the C function resolved at the call (a test may put a sentinel)
                return (real_getaddrinfo if _name == "getaddrinfo" else getattr(_socket, _name))(host, *a, **kw)
            _refuse(f"name lookup socket.{_name}", repr(host)[:80])
        monkeypatch.setattr(socket, name, lookup)

    def nameinfo(sockaddr, *a, **kw):                  # K4a (RV2-7): a reverse lookup of a non-loopback address
        if isinstance(sockaddr, tuple) and sockaddr and sockaddr[0] in LOOPBACK:
            return _socket.getnameinfo(sockaddr, *a, **kw)
        _refuse("name lookup socket.getnameinfo", repr(sockaddr)[:80])
    monkeypatch.setattr(socket, "getnameinfo", nameinfo)
    # fix-K-gated G2: a datagram needs no connect; sendto / sendmsg to an internet address is refused
    for name in ("sendto", "sendmsg"):
        real = getattr(socket.socket, name)

        def send(self, *a, _real=real, _name=name, **kw):
            if self.family in (socket.AF_INET, socket.AF_INET6):
                _refuse(f"socket {_name}", repr(a[-1] if a else None)[:80])
            return _real(self, *a, **kw)
        monkeypatch.setattr(socket.socket, name, send)
    monkeypatch.setattr(socket.socket, "connect", lambda self, address: _refuse("socket connect", repr(address)[:80]))
    monkeypatch.setattr(socket.socket, "connect_ex", lambda self, address: _refuse("socket connect_ex", repr(address)[:80]))
    monkeypatch.setattr(socket, "create_connection", lambda address, *a, **kw: _refuse("socket connection", repr(address)[:80]))
    monkeypatch.setattr(urllib.request.OpenerDirector, "open",
                        lambda self, fullurl, *a, **kw: _refuse("urllib open", repr(getattr(fullurl, "full_url", fullurl))[:80]))
    try:
        yield allowed
    finally:
        allowed.clear()                                # the flag never outlives the test that set it


@pytest.fixture
def local_processes(pp10_guard):
    """Permit the kit's own interpreter(s) and git, by exact path, for this test only (a real local process; no
    network). Both layers read the same list (ALLOWED); pp10_guard empties it when the test ends."""
    pp10_guard.extend(LOCAL_PROGRAMS)
    return tuple(LOCAL_PROGRAMS)
