"""K4a: conftest.py's process-wide layer (the core re-verifier's DK-1 and DK-2; the security re-verifier's RV2-6 and
RV2-7). The audit hook, the fork_exec refusal and the socket wrappers hold at collection, in a module-scoped fixture,
for multiprocessing's spawn and for direct os and C-level calls, and the flag (ALLOWED) opens exact paths only.

Fail-closed by design: every probe either raises the audit event by hand (sys.audit: nothing real happens), targets a
missing program path (a weakened guard gets FileNotFoundError, never a started program), uses numeric-only lookup
flags (no DNS query), or loopback only; the few real socket calls to a non-loopback numeric address run only after the
same event raised by hand is refused (so a weakened hook fails before any packet; the mutation runs add a sandbox). No probe calls a real os.fork,
os.system or a reverse lookup. Every token-free; nothing here reaches the network."""
from __future__ import annotations

import _socket
import contextlib
import multiprocessing
import multiprocessing.spawn
import multiprocessing.util
import os
import re
import socket
import subprocess
import sys
import threading
import types
import urllib.request

import pytest

import conftest

MISSING = "/nonexistent-pp10-k4a/bin"          # no such folder: a program here can never start
REAL_POPEN_INIT = subprocess.Popen.__init__     # bound at collection, before any test's fixture
REAL_EXECV = os.execv
REAL_POSIX_SPAWN = getattr(os, "posix_spawn", None)
REAL_OPEN = urllib.request.OpenerDirector.open
PROCESS_WIDE_SOCKET = {name: getattr(socket.socket, name) for name in ("connect", "connect_ex", "sendto", "sendmsg")}
HOOK = conftest.HOOK_PREFIX


def _outcome(call) -> tuple[str, str]:
    try:
        call()
    except conftest.NetworkOrProcessRefused as exc:
        return "refused", str(exc)
    except BaseException as exc:                # noqa: BLE001 - recorded, the test fails on it
        return "other", type(exc).__name__
    return "ran", ""


def _popen(argv, **kw):
    """subprocess.Popen's REAL __init__ (bound at collection), past the per-test fixture: only the process-wide layer
    stands between this call and a fork."""
    return REAL_POPEN_INIT(subprocess.Popen.__new__(subprocess.Popen), argv, **kw)


def _sock(family):
    return types.SimpleNamespace(family=family)


def _hook_refuses(event: str, *args) -> bool:
    try:
        sys.audit(event, *args)
    except conftest.NetworkOrProcessRefused:
        return True
    return False


def _only_if_the_hook_refuses(event: str, family, address, call):
    """A real socket call to a NON-loopback address runs only after the same event, raised by hand, is refused by
    the hook (and the address is not taken for loopback): a weakened hook fails here, before any packet."""
    if conftest.loopback_host(address[0]) or not _hook_refuses(event, _sock(family), address):
        raise AssertionError(f"the hook would let {event} to {address!r} through: the real call is not made")
    return call()


def _socket_call(family, kind, method, *args):
    with socket.socket(family, kind) as sock:
        return _only_if_the_hook_refuses("socket." + method, family, args[-1], lambda: getattr(sock, method)(*args))


# At this module's import (collection): no fixture exists yet, so only the process-wide layer can refuse these.
AT_COLLECTION = {
    "subprocess": _outcome(lambda: subprocess.run([MISSING + "/ssh", "-V"], capture_output=True)),
    "interpreter": _outcome(lambda: sys.audit("subprocess.Popen", sys.executable, [sys.executable, "-c", "pass"],
                                              None, None)),
    "os.system": _outcome(lambda: sys.audit("os.system", b"ssh -V")),
    "lookup": _outcome(lambda: socket.getaddrinfo("203.0.113.9", 22, flags=socket.AI_NUMERICHOST)),
    "connect": _outcome(lambda: _socket_call(socket.AF_INET, socket.SOCK_STREAM, "connect", ("203.0.113.9", 22))),
    "urllib": _outcome(lambda: urllib.request.urlopen("http://127.0.0.1:9/", timeout=1)),
    "spawnv": _outcome(lambda: multiprocessing.util.spawnv_passfds(MISSING + "/python", [MISSING + "/python"], [])),
}


@pytest.fixture(scope="module")
def module_scoped_probes():
    """Set up before the first test that requests it, BEFORE that test's function-scoped pp10_guard (pytest orders
    the wider scope first): the per-test fixture is not active here."""
    return {"subprocess": _outcome(lambda: subprocess.run([MISSING + "/scp"], capture_output=True)),
            "execv": _outcome(lambda: os.execv(MISSING + "/true", ["true"])),
            "posix_spawn": _outcome(lambda: os.posix_spawn(MISSING + "/true", ["true"], {}))
            if hasattr(os, "posix_spawn") else ("refused", HOOK + "(no posix_spawn here)"),
            "getnameinfo": _outcome(lambda: socket.getnameinfo(("203.0.113.9", 22),
                                                               socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)),
            "sendto": _outcome(lambda: _socket_call(socket.AF_INET, socket.SOCK_DGRAM, "sendto", b"x", ("203.0.113.9", 9))),
            "fixture_active": subprocess.Popen.__init__ is not REAL_POPEN_INIT}


def test_dk1_collection_time_calls_stop_in_the_process_wide_layer():
    for name, (verdict, text) in AT_COLLECTION.items():
        assert verdict == "refused", (name, verdict, text)
        assert text.startswith(HOOK), (name, text)
    assert "socket connect (before any name resolution)" in AT_COLLECTION["connect"][1]   # the wrapper, before C
    assert "fork_exec (multiprocessing's spawn)" in AT_COLLECTION["spawnv"][1]
    assert "executable = " + repr(sys.executable) in AT_COLLECTION["interpreter"][1]  # no local_processes at collection


def test_dk1_module_scoped_fixture_calls_stop_in_the_process_wide_layer(module_scoped_probes):
    probes = dict(module_scoped_probes)
    assert probes.pop("fixture_active") is False                  # the per-test fixture was not set up yet
    for name, (verdict, text) in probes.items():
        assert verdict == "refused" and text.startswith(HOOK), (name, verdict, text)


REFUSED_EVENTS = [
    ("subprocess.Popen", ("/usr/bin/ssh", ["ssh", "-V"], None, None)),
    ("subprocess.Popen", (sys.executable, [sys.executable, "-c", "pass"], None, None)),      # no local_processes
    ("subprocess.Popen", ("/bin/sh", ["/bin/sh", "-c", "true"], None, None)),
    ("os.system", (b"true",)),
    ("os.exec", ("/usr/bin/true", ["true"], None)),
    ("os.posix_spawn", ("/usr/bin/true", ["true"], {})),
    ("os.spawn", (os.P_WAIT, "/usr/bin/true", ["true"], None)),
    ("os.fork", ()),
    ("os.forkpty", ()),
    ("socket.connect", (_sock(socket.AF_INET), ("203.0.113.9", 22))),
    ("socket.connect", (_sock(socket.AF_INET), ("huggingface.co", 443))),
    ("socket.connect", (_sock(socket.AF_INET), ("0.0.0.0", 22))),
    ("socket.connect", (_sock(socket.AF_INET6), ("2001:db8::1", 22, 0, 0))),
    ("socket.connect", (_sock(socket.AF_INET), ("localhost.attacker.example", 80))),
    ("socket.sendto", (_sock(socket.AF_INET), ("203.0.113.9", 53))),
    ("socket.sendto", (_sock(socket.AF_INET6), ("2001:db8::1", 53, 0, 0))),
    ("socket.sendmsg", (_sock(socket.AF_INET), ("203.0.113.9", 53))),
    ("socket.getaddrinfo", ("huggingface.co", 443, 0, 0, 0)),
    ("socket.getaddrinfo", ("203.0.113.9", 22, 0, 0, 0)),
    ("socket.getaddrinfo", ("", 80, 0, 0, 0)),
    ("socket.gethostbyname", ("api.runpod.io",)),
    ("socket.gethostbyaddr", ("203.0.113.9",)),
    ("socket.getnameinfo", (("203.0.113.9", 22),)),
    ("urllib.Request", ("https://huggingface.co/api/whoami-v2", None, {}, "GET")),
    ("urllib.Request", ("http://127.0.0.1:9/", None, {}, "GET")),                        # every urllib open
    ("http.client.connect", (None, "huggingface.co", 443)),
]


@pytest.mark.parametrize("event, args", REFUSED_EVENTS, ids=[f"{e}-{i}" for i, (e, _) in enumerate(REFUSED_EVENTS)])
def test_dk1_the_audit_hook_refuses_each_way_out(event, args):
    """Each event raised by hand: the hook refuses it (no real call is made, so a weakened hook starts nothing)."""
    with pytest.raises(conftest.NetworkOrProcessRefused) as info:
        sys.audit(event, *args)
    assert str(info.value).startswith(HOOK)


ALLOWED_EVENTS = [
    ("socket.connect", (_sock(socket.AF_INET), ("127.0.0.1", 9))),
    ("socket.connect", (_sock(socket.AF_INET), ("127.8.9.10", 9))),
    ("socket.connect", (_sock(socket.AF_INET6), ("::1", 9, 0, 0))),
    ("socket.connect", (_sock(socket.AF_INET), ("localhost", 9))),
    ("socket.connect", (_sock(socket.AF_UNIX), "/tmp/pp10-k4a.sock")),
    ("socket.sendmsg", (_sock(socket.AF_INET), None)),                  # a connected socket: its connect was checked
    ("socket.getaddrinfo", (None, 80, 0, 0, 0)),
    ("socket.getaddrinfo", ("localhost", 80, 0, 0, 0)),
    ("socket.getaddrinfo", (b"127.0.0.1", 80, 0, 0, 0)),
    ("socket.gethostbyname", ("127.0.0.1",)),
    ("socket.gethostbyaddr", ("::1",)),
    ("socket.getnameinfo", (("127.0.0.1", 9),)),
    ("http.client.connect", (None, "127.0.0.1", 9)),
    ("open", ("/dev/null", "r", 0)),                                     # an event the hook does not read
]


@pytest.mark.parametrize("event, args", ALLOWED_EVENTS, ids=[f"{e}-{i}" for i, (e, _) in enumerate(ALLOWED_EVENTS)])
def test_dk1_the_audit_hook_lets_loopback_and_local_calls_through(event, args):
    sys.audit(event, *args)


def test_dk1_real_calls_past_the_fixture_reach_the_hook(tmp_path, monkeypatch):
    """The real calls raise the events the hook reads (wiring): past the per-test fixture (the functions bound at
    collection), each refuses in the process-wide layer; the loopback ones reach the hook and are recorded."""
    for argv, kw in (([MISSING + "/ssh", "-V"], {}), ([MISSING + "/curl"], {"shell": False}),
                     ([sys.executable, "-c", "pass"], {})):
        verdict, text = _outcome(lambda: _popen(argv, **kw))
        assert verdict == "refused" and text.startswith(HOOK + "the kit's tests never start a real subprocess"), text
    assert _outcome(lambda: REAL_EXECV(MISSING + "/true", ["true"]))[1].startswith(HOOK)
    if REAL_POSIX_SPAWN is not None:
        assert _outcome(lambda: REAL_POSIX_SPAWN(MISSING + "/true", ["true"], {}))[1].startswith(HOOK)
    assert _outcome(lambda: REAL_OPEN(urllib.request.build_opener(), "http://127.0.0.1:9/", timeout=1))[1].startswith(HOOK)
    assert _outcome(lambda: _socket.getaddrinfo("203.0.113.9", 22, 0, 0, 0, socket.AI_NUMERICHOST))[1].startswith(HOOK)
    # C-level sockets: a non-loopback numeric address refuses at the hook (the address parses with no DNS query)
    with contextlib.closing(_socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as raw:
        assert _outcome(lambda: _only_if_the_hook_refuses("socket.connect", socket.AF_INET, ("203.0.113.9", 22),
                                                          lambda: raw.connect(("203.0.113.9", 22))))[1].startswith(
            HOOK + "the kit's tests never start "
                                                                                      "a real socket.connect")
    # loopback reaches the hook and is let through (the OS refuses the closed port; nothing leaves the machine)
    SEEN = conftest.SEEN
    SEEN.clear()
    with contextlib.closing(_socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as raw:
        assert raw.connect_ex(("127.0.0.1", 9)) != 0
    with contextlib.closing(_socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as udp:
        try:
            udp.sendto(b"x", ("127.0.0.1", 9))
        except OSError:                          # a sandbox that denies loopback too (EPERM); the event came first
            pass
    _socket.getaddrinfo("127.0.0.1", 9, 0, 0, 0, socket.AI_NUMERICHOST)
    _socket.getnameinfo(("127.0.0.1", 9), socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)
    events = [e for e, _ in SEEN]
    for event in ("socket.connect", "socket.sendto", "socket.getaddrinfo", "socket.getnameinfo"):
        assert event in events, (event, list(SEEN))


def test_dk1_multiprocessing_spawn_is_refused_before_any_child(monkeypatch):
    """The Mac's default start method is spawn; its child starts through _posixsubprocess.fork_exec (no audit event).
    The executable is a missing path, so a weakened guard gets an error, never a second interpreter."""
    monkeypatch.setattr(multiprocessing.spawn, "_python_exe", MISSING + "/python")
    ctx = multiprocessing.get_context("spawn")
    process = ctx.Process(target=print, args=("never",))
    verdict, text = _outcome(process.start)
    assert verdict == "refused" and "fork_exec (multiprocessing's spawn)" in text, (verdict, text)
    import _posixsubprocess
    assert _posixsubprocess.fork_exec is conftest._fork_exec_refused
    assert subprocess._fork_exec is not conftest._fork_exec_refused       # subprocess keeps its own, behind its event


def test_dk1_the_socket_methods_are_wrapped_process_wide():
    """Before the C call (which resolves a host name first): the four socket.socket methods outside any test's
    fixture are the process-wide wrappers, not _socket's."""
    for name, method in PROCESS_WIDE_SOCKET.items():
        assert getattr(method, "pp10_process_wide", False) is True and method is not getattr(_socket.socket, name), name


def test_dk2_local_processes_opens_exact_paths_only_in_both_layers(local_processes, tmp_path):
    """The core re-verifier's DK-2: a file with an allowed program's BASE name elsewhere is refused, by the per-test
    fixture (its message) and by the process-wide hook (its message); so are a shell and executable= behind an allowed
    argv[0] (RV2-7). Each target is a missing file, so a weakened check gets FileNotFoundError, never a program."""
    assert conftest.ALLOWED == list(local_processes)
    for program in local_processes:
        lookalike = str(tmp_path / os.path.basename(program))
        with pytest.raises(conftest.NetworkOrProcessRefused, match=r"^PP10: .*subprocess \(argv\[0\] = "):
            subprocess.run([lookalike, "-c", "pass"], capture_output=True)
        with pytest.raises(conftest.NetworkOrProcessRefused, match="^" + re.escape(HOOK)):
            sys.audit("subprocess.Popen", lookalike, [lookalike], None, None)
        assert not conftest.program_allowed(lookalike) and conftest.program_allowed(program)
    with pytest.raises(conftest.NetworkOrProcessRefused, match=r"^PP10: .*argv\[0\] = '/bin/sh'"):
        subprocess.run(["/bin/sh", "-c", "true"])
    with pytest.raises(conftest.NetworkOrProcessRefused, match=r"^PP10: .*executable = '" + MISSING + "/echo'"):
        subprocess.run([sys.executable, "-c", "pass"], executable=MISSING + "/echo")
    with pytest.raises(conftest.NetworkOrProcessRefused, match="^" + re.escape(HOOK)):             # past the fixture: the hook
        _popen([sys.executable, "-c", "pass"], executable=MISSING + "/echo")
    with pytest.raises(conftest.NetworkOrProcessRefused, match="^" + re.escape(HOOK)):
        sys.audit("subprocess.Popen", "/usr/bin/ssh", ["ssh"], None, None)               # NEVER, even if listed
    done = subprocess.run([sys.executable, "-B", "-c", "print(6 * 7)"], capture_output=True, text=True)
    assert done.returncode == 0 and done.stdout.strip() == "42"                          # the exact path still runs


def test_dk1_the_flag_never_outlives_the_test_that_set_it():
    """Runs after the local_processes test above (file order): ALLOWED is empty again, so the hook refuses the
    interpreter (and a module-scoped fixture set up between two tests sees an empty flag)."""
    assert conftest.ALLOWED == []
    with pytest.raises(conftest.NetworkOrProcessRefused, match="^" + re.escape(HOOK)):
        sys.audit("subprocess.Popen", sys.executable, [sys.executable, "-c", "pass"], None, None)


def test_dk1_the_state_is_shared_and_installed_once():
    state = sys.__dict__["_pp10_stage1_78b_guard"]
    assert state["installed"] is True and state["allowed"] is conftest.ALLOWED and state["seen"] is conftest.SEEN
    assert conftest.loopback_host("127.0.0.1") and conftest.loopback_host("::1") and conftest.loopback_host(b"localhost")
    for host in ("", None, "203.0.113.9", "0.0.0.0", "localhost.example", "::ffff:203.0.113.9", "huggingface.co", 7):
        assert not conftest.loopback_host(host), host



# ===== round 4b: the security verifier's D1 and D2 (fail-closed probes; no real call is ever made) ==================
# D1: the process-wide WRAPPER's address check for sendto, sendmsg and AF_INET6 sockets. Each probe calls the wrapper
# bound at collection on a stand-in object (no socket): the wrapper must refuse before the C call; a weakened wrapper
# reaches _socket's C method, which raises TypeError on the stand-in (no packet, no lookup), so the probe fails.
NAME = "pp10-k4b.invalid"                       # a reserved name: never resolves
V6 = ("2001:db8::1", 53, 0, 0)                  # the IPv6 documentation prefix
WRAP = "(before any name resolution)"


class _Stand:
    def __init__(self, family):
        self.family = family


WRAPPER_CASES = {
    "sendto-v4-name": ("sendto", socket.AF_INET, (b"x", (NAME, 53))),
    "sendto-v4-flags-name": ("sendto", socket.AF_INET, (b"x", 0, (NAME, 53))),
    "sendto-v6-name": ("sendto", socket.AF_INET6, (b"x", (NAME, 53))),
    "sendto-v6-flags-numeric": ("sendto", socket.AF_INET6, (b"x", 0, V6)),
    "sendmsg-v4-name": ("sendmsg", socket.AF_INET, ([b"x"], [], 0, (NAME, 53))),
    "sendmsg-v6-name": ("sendmsg", socket.AF_INET6, ([b"x"], [], 0, (NAME, 53))),
    "sendmsg-v6-numeric": ("sendmsg", socket.AF_INET6, ([b"x"], [], 0, V6)),
    "connect-v6-name": ("connect", socket.AF_INET6, ((NAME, 9),)),
    "connect_ex-v6-numeric": ("connect_ex", socket.AF_INET6, (V6[:2] + (0, 0),)),
}


def _wrapper_probes() -> dict:
    return {key: _outcome(lambda m=m, fam=fam, a=a: PROCESS_WIDE_SOCKET[m](_Stand(fam), *a))
            for key, (m, fam, a) in WRAPPER_CASES.items()}


# D2: the hook itself (events raised by hand: nothing real happens) under the local_processes flag, in a non-main
# thread, and for host names given as bytes.
HOOK_EVENTS = [
    ("os.system", (b"true",)), ("os.exec", ("/usr/bin/true", ["true"], None)),
    ("os.posix_spawn", ("/usr/bin/true", ["true"], {})), ("os.spawn", (os.P_WAIT, "/usr/bin/true", ["true"], None)),
    ("os.fork", ()), ("os.forkpty", ()), ("subprocess.Popen", ("/usr/bin/ssh", ["ssh"], None, None)),
    ("socket.connect", (_sock(socket.AF_INET), ("203.0.113.9", 22))),
    ("socket.connect", (_sock(socket.AF_INET6), V6)),
    ("socket.sendto", (_sock(socket.AF_INET6), V6)), ("socket.sendmsg", (_sock(socket.AF_INET), ("203.0.113.9", 53))),
    ("socket.getaddrinfo", (NAME, 80, 0, 0, 0)), ("socket.gethostbyname", (NAME,)),
    ("socket.gethostbyaddr", ("203.0.113.9",)), ("socket.getnameinfo", (("203.0.113.9", 22),)),
    ("urllib.Request", ("https://huggingface.co/", None, {}, "GET")), ("http.client.connect", (None, NAME, 443)),
]
BYTES_EVENTS = [
    ("socket.getaddrinfo", (NAME.encode(), 80, 0, 0, 0)), ("socket.getaddrinfo", (b"203.0.113.9", 80, 0, 0, 0)),
    ("socket.gethostbyname", (NAME.encode(),)), ("socket.connect", (_sock(socket.AF_INET), (NAME.encode(), 80))),
    ("socket.sendto", (_sock(socket.AF_INET6), (b"2001:db8::1", 53, 0, 0))),
    ("http.client.connect", (None, b"203.0.113.9", 80)),
]


def _hook_probes(events) -> list:
    return [(event, _outcome(lambda e=event, a=args: sys.audit(e, *a))) for event, args in events]


def _in_thread(probe):
    box = {}
    worker = threading.Thread(target=lambda: box.update(result=probe()), name="pp10-k4b-probe")
    worker.start()
    worker.join(30)
    assert not worker.is_alive()
    return box["result"]


AT_COLLECTION_WRAPPERS = _wrapper_probes()
AT_COLLECTION_THREAD = _in_thread(lambda: _hook_probes(HOOK_EVENTS + BYTES_EVENTS) + [
    ("wrapper", v) for v in _wrapper_probes().values()])


@pytest.fixture(scope="module")
def module_wrapper_probes():
    return _wrapper_probes()


def _all_refused(results, where: str) -> None:
    bad = [(where, name, verdict, text[:120]) for name, (verdict, text) in results
           if verdict != "refused" or not text.startswith(HOOK)]
    assert bad == []


def test_k4bf_d1_the_wrapper_refuses_sendto_sendmsg_and_inet6_before_any_resolution(module_wrapper_probes):
    """D1: at collection and in a module-scoped fixture (only the process-wide layer exists there), the wrapper of each
    of sendto (with and without flags), sendmsg and an AF_INET6 connect / connect_ex refuses a host name or a
    non-loopback address before the C call (its message names the wrapper)."""
    for where, results in (("collection", AT_COLLECTION_WRAPPERS), ("module fixture", module_wrapper_probes)):
        _all_refused(results.items(), where)
        assert all(WRAP in text for _, text in results.values()), where
    loopback = PROCESS_WIDE_SOCKET["sendto"]           # loopback passes the wrapper (and reaches C, which rejects the
    with pytest.raises(TypeError):                     # stand-in: nothing is sent)
        loopback(_Stand(socket.AF_INET6), b"x", ("::1", 9, 0, 0))


def test_k4bf_d2_the_hook_refuses_under_the_flag(local_processes):
    """D2: under local_processes (ALLOWED holds the interpreters and git) the hook still refuses os.system, exec,
    posix_spawn, spawn, fork, forkpty, ssh, sockets to non-loopback addresses, lookups of names, urllib and
    http.client (the per-test fixture patches only Python names; posix.* and _socket meet the hook alone)."""
    assert conftest.ALLOWED
    _all_refused(_hook_probes(HOOK_EVENTS), "under the flag")
    _all_refused(_hook_probes(BYTES_EVENTS), "under the flag, bytes hosts")


def test_k4bf_d2_the_hook_refuses_in_a_non_main_thread_and_for_bytes_hosts():
    """D2: a thread started at collection and one started in a test meet the same hook; host names given as bytes are
    no loopback (only b"localhost" and loopback IPs are)."""
    _all_refused(AT_COLLECTION_THREAD, "collection thread")
    _all_refused(_in_thread(lambda: _hook_probes(HOOK_EVENTS + BYTES_EVENTS)), "test thread")
    _all_refused(_hook_probes(BYTES_EVENTS), "main thread, bytes hosts")
    for host in (NAME.encode(), b"203.0.113.9", b"localhost.example", b"2001:db8::1", b""):
        assert not conftest.loopback_host(host), host
    assert conftest.loopback_host(b"127.0.0.1") and conftest.loopback_host(b"::1")
