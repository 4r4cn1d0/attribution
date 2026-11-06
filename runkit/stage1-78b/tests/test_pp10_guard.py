"""PP10: the guard in conftest.py fails any real subprocess start, os.system, socket connect or urllib open during the
kit's tests unless a test has replaced the call with a fake. The K3 development incident's path (host.gated_download's
default runner, subprocess.run bound at import in the file of that day, a real ``ssh`` to 203.0.113.9 with a fake
token) is exercised here WITHOUT a fake and must stop inside the guard: no process starts. Every token is fake."""
from __future__ import annotations

import functools
import importlib
import os
import socket
import subprocess
import sys
import urllib.request

import pytest

import conftest
from test_stage1_runkit import w, fake_token  # noqa: F401

RUN_BOUND_AT_IMPORT = subprocess.run          # the K3 incident's binding form: resolved before any test's patch
# K4a (RV2-6): every callable a probe below goes through, as bound at collection (before any test's guard). Each probe
# first checks that the per-test guard has replaced it, so a weakened guard fails the test before any real call.
BOUND_AT_IMPORT = {"socket.socket." + name: getattr(socket.socket, name) for name in ("connect", "connect_ex", "sendto",
                                                                                      "sendmsg")}
BOUND_AT_IMPORT.update({"socket.create_connection": socket.create_connection,
                        "OpenerDirector.open": urllib.request.OpenerDirector.open,
                        "subprocess.Popen.__init__": subprocess.Popen.__init__, "os.system": os.system})


def _current(name: str):
    owner, _, attr = name.rpartition(".")
    return getattr({"socket.socket": socket.socket, "socket": socket, "OpenerDirector": urllib.request.OpenerDirector,
                    "subprocess.Popen": subprocess.Popen, "os": os}[owner], attr)


def _assert_guarded(names) -> None:
    for name in names:
        assert _current(name) is not BOUND_AT_IMPORT[name], f"{name} is not replaced by the per-test guard"


def test_the_k3_incident_path_stops_in_the_guard_without_a_fake(w, monkeypatch):
    """host.gated_download(host, token) with no runner= resolves subprocess.run at the call and would start ``ssh`` to
    the host's address; under PP10 the guard refuses before any process starts, and no record is written."""
    w.init()                                                                       # a plan, so hosts/<host>/ resolves
    host = importlib.import_module("host")
    monkeypatch.setattr(host, "ssh_base", lambda hh: ["-p", "22", "root@203.0.113.9"])   # TEST-NET-3, as in the incident
    token = fake_token()
    with pytest.raises(conftest.NetworkOrProcessRefused, match=r"subprocess \(argv\[0\] = 'ssh'\)"):
        host.gated_download("olmo2-7b-0-1", token)
    assert not (w.root / "hosts" / "olmo2-7b-0-1" / "gated-download.json").exists()
    # the same through the CLI entry with a real subprocess module (the incident's exact path: a patched name elsewhere
    # does not reach this module's subprocess.run)
    with pytest.raises(conftest.NetworkOrProcessRefused, match="argv\\[0\\] = 'ssh'"):
        host.gated_download("olmo2-7b-0-1", token, runner=RUN_BOUND_AT_IMPORT)
    assert not (w.root / "hosts" / "olmo2-7b-0-1" / "gated-download.json").exists()


def test_every_real_exit_from_the_process_is_refused(tmp_path):
    _assert_guarded(BOUND_AT_IMPORT)                         # RV2-6: before any probe, every path is the guard's
    for call in (lambda: subprocess.run(["ssh", "-V"], capture_output=True),
                 lambda: subprocess.Popen(["caffeinate", "-i", "true"]),
                 lambda: subprocess.check_output(["gh", "--version"]),
                 lambda: subprocess.call("ssh -V", shell=True),
                 lambda: RUN_BOUND_AT_IMPORT(["scp", "-V"], capture_output=True),
                 lambda: os.popen("ssh -V").read(),
                 lambda: os.system("ssh -V"),
                 lambda: socket.create_connection(("127.0.0.1", 9), timeout=1),      # RV2-6: loopback targets only
                 lambda: socket.socket().connect(("127.0.0.1", 9)),
                 lambda: socket.socket().connect_ex(("127.0.0.1", 9)),
                 lambda: urllib.request.urlopen("http://203.0.113.9/", timeout=1),
                 lambda: urllib.request.build_opener().open("https://huggingface.co/api/whoami-v2", timeout=1),
                 lambda: urllib.request.urlopen(urllib.request.Request("https://api.runpod.io/graphql"), timeout=1)):
        with pytest.raises(conftest.NetworkOrProcessRefused, match="PP10"):
            call()
    if hasattr(os, "posix_spawn"):
        with pytest.raises(conftest.NetworkOrProcessRefused, match="PP10"):
            os.posix_spawn("/bin/true", ["true"], {})
    # the kit's own interpreter is refused too unless the test asks for local processes
    with pytest.raises(conftest.NetworkOrProcessRefused, match="PP10"):
        subprocess.run([sys.executable, "-c", "pass"])


def test_a_fake_never_reaches_the_guard(w, monkeypatch):
    """The tests' established forms of replacing a call: the module's subprocess name, runner=, run=, get= (the kit's
    functions take them). None starts a process, so the guard is never touched."""
    w.init()                                                                       # hosts/<host>/ exists under a plan
    host = importlib.import_module("host")
    launch = importlib.import_module("launch")
    seen = []

    def runner(args, **kwargs):
        seen.append(list(args))
        return subprocess.CompletedProcess(args, 0, "{}", "")
    monkeypatch.setattr(host, "ssh_base", lambda hh: ["-p", "22", "root@203.0.113.9"])
    record = host.gated_download("olmo2-7b-0-1", fake_token(), runner=runner)
    assert record["ok"] is True and seen[0][0] == "ssh"
    fake_module = type(subprocess)("subprocess")
    fake_module.run, fake_module.DEVNULL = runner, subprocess.DEVNULL
    monkeypatch.setattr(host, "subprocess", fake_module)
    assert host.gated_download("olmo2-7b-0-1", fake_token())["ok"] is True and len(seen) == 2
    assert callable(getattr(launch, "token_checks", None))                        # takes get= (K3); not exercised here


def test_local_processes_permits_the_kits_interpreter_and_git_only(local_processes):
    done = subprocess.run([sys.executable, "-B", "-c", "print(2 + 2)"], capture_output=True, text=True)
    assert done.returncode == 0 and done.stdout.strip() == "4"
    assert sys.executable in local_processes and "git" in local_processes
    for argv in (["ssh", "-V"], ["scp", "-V"], ["gh", "--version"], ["curl", "--version"], ["caffeinate", "-i", "true"],
                 ["runpodctl", "version"], ["python3", "-c", "pass"]):
        with pytest.raises(conftest.NetworkOrProcessRefused, match="PP10"):
            subprocess.run(argv, capture_output=True)
    with pytest.raises(conftest.NetworkOrProcessRefused):                          # the network stays refused
        urllib.request.urlopen("http://203.0.113.9/", timeout=1)
    with pytest.raises(conftest.NetworkOrProcessRefused):
        os.system("true")


def test_the_guard_is_on_by_default_and_names_the_rule():
    with pytest.raises(conftest.NetworkOrProcessRefused) as info:
        subprocess.run(["ssh", "-V"])
    text = str(info.value)
    assert text.startswith("PP10: the kit's tests never start a real subprocess (argv[0] = 'ssh')")
    assert "replace it with a fake" in text and "local_processes" in text
    assert issubclass(conftest.NetworkOrProcessRefused, RuntimeError)
    assert "ssh" in conftest.NEVER and "python3" in conftest.NEVER and "git" in conftest.LOCAL_PROGRAMS
    assert functools.partial(subprocess.run, ["ssh"]) is not None               # binding a partial is not a start


def test_the_kits_modules_spawn_nothing_at_import(w, monkeypatch):
    """Importing every kit MODULE under the guard starts no process and opens no connection (an import-time spawn
    would fail this test). account.py is a script (byte-identical to the stage-1 kit's): it calls the RunPod API at
    module level, so importing it under the guard with a FAKE key must stop in the guard's urllib refusal. status.py
    is a script too (it reads plan.json at import), so the World's plan is written first."""
    w.init()
    for name in ("budget", "host", "launch", "orchestrate", "pack_setup", "plan_tool", "finisher",
                 "states_tool", "status", "backup_records_stage1", "probes", "secret_scan", "seal", "gateb_mac"):
        assert importlib.import_module(name)
    monkeypatch.setenv("RUNPOD_OPERATOR_API_KEY", "fake-key-for-this-test-only")
    sys.modules.pop("account", None)
    with pytest.raises(conftest.NetworkOrProcessRefused, match=r"urllib open \('https://api.runpod.io/graphql'\)"):
        importlib.import_module("account")
    sys.modules.pop("account", None)



REAL_OS = {name: getattr(os, name) for name in ("fork", "forkpty", "execv", "execve", "posix_spawn", "posix_spawnp")
           if hasattr(os, name)}                      # bound at import, before any test's guard
REAL_GETADDRINFO = socket.getaddrinfo
LOOKUPS = ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr")
REAL_LOOKUPS = {name: getattr(socket, name) for name in LOOKUPS + ("getnameinfo",)}   # bound at collection (RV2-6)


def _sentinels(monkeypatch) -> None:
    """Put a sentinel under every name lookup (the C functions the guard and the stdlib call at the call): if a guard
    were weakened, the call would stop here with an AssertionError, never send a DNS query."""
    import _socket

    def reached(*a, **kw):
        raise AssertionError("a real name lookup was reached (the guard let it through)")
    for name in LOOKUPS + ("getnameinfo",):
        monkeypatch.setattr(_socket, name, reached)


def test_g1_g4_name_lookups_datagrams_forks_and_execs_are_refused_too(monkeypatch):
    """fix-K-gated G1-G4: a DNS lookup sends a query before any connect (G1); a datagram socket sends with no connect
    (G2); a fork or an exec leaves the guarded process (G3); each spawn refusal names its own call (G4). Loopback name
    lookups and None stay local and pass. Safe under a weakened guard too: each fork/exec/spawn function is first
    checked to be replaced (so a real one is never called), the lookups sit over sentinels, and the datagrams go to the
    loopback discard port (no packet leaves the machine)."""
    for name, real in REAL_OS.items():
        assert getattr(os, name) is not real, f"os.{name} is not guarded"
    for name, real in REAL_LOOKUPS.items():                  # RV2-6: socket.gethostbyname & co. ARE _socket's functions,
        assert getattr(socket, name) is not real, f"socket.{name} is not guarded"   # so a sentinel cannot sit under them
    _assert_guarded([n for n in BOUND_AT_IMPORT if n.startswith("socket.socket.")])
    assert "sendto" in vars(socket.socket) and "sendmsg" in vars(socket.socket)
    assert socket.getaddrinfo is not REAL_GETADDRINFO
    assert socket.getaddrinfo("localhost", 80) and socket.getaddrinfo(None, 80)     # local: no packet leaves
    assert socket.gethostbyname("127.0.0.1") == "127.0.0.1"
    assert socket.getnameinfo(("127.0.0.1", 9), socket.NI_NUMERICHOST | socket.NI_NUMERICSERV) == ("127.0.0.1", "9")
    _sentinels(monkeypatch)
    for call, what in ((lambda: socket.getaddrinfo("huggingface.co", 443), "name lookup socket.getaddrinfo"),
                       (lambda: socket.getaddrinfo("203.0.113.9", 22), "name lookup socket.getaddrinfo"),
                       (lambda: socket.gethostbyname("api.runpod.io"), "name lookup socket.gethostbyname"),
                       (lambda: socket.gethostbyname_ex("huggingface.co"), "name lookup socket.gethostbyname_ex"),
                       (lambda: socket.gethostbyaddr("203.0.113.9"), "name lookup socket.gethostbyaddr"),
                       (lambda: socket.getnameinfo(("203.0.113.9", 22), socket.NI_NUMERICHOST | socket.NI_NUMERICSERV),
                        "name lookup socket.getnameinfo"),                                  # RV2-7: a reverse lookup
                       (lambda: os.fork(), "os.fork"),
                       (lambda: os.execv("/usr/bin/true", ["true"]), "os.execv"),
                       (lambda: os.execve("/usr/bin/true", ["true"], {}), "os.execve"),
                       (lambda: os.execvp("true", ["true"]), "os.execv"),            # execvp goes through execv
                       (lambda: os.execl("/usr/bin/true", "true"), "os.execv"),
                       (lambda: os.spawnv(os.P_WAIT, "/usr/bin/true", ["true"]), "os.fork")):   # spawnv forks first
        with pytest.raises(conftest.NetworkOrProcessRefused, match="PP10: the kit's tests never start a real " + what):
            call()
    if "forkpty" in REAL_OS:
        with pytest.raises(conftest.NetworkOrProcessRefused, match="real os.forkpty"):
            os.forkpty()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        with pytest.raises(conftest.NetworkOrProcessRefused, match=r"real socket sendto \(\('127.0.0.1', 9\)\)"):
            udp.sendto(b"x", ("127.0.0.1", 9))
        with pytest.raises(conftest.NetworkOrProcessRefused, match="real socket sendmsg"):
            udp.sendmsg([b"x"], [], 0, ("127.0.0.1", 9))
    with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as udp6:                    # RV2-7: IPv6 datagrams too
        with pytest.raises(conftest.NetworkOrProcessRefused, match=r"real socket sendto \(\('::1', 9, 0, 0\)\)"):
            udp6.sendto(b"x", ("::1", 9, 0, 0))
        with pytest.raises(conftest.NetworkOrProcessRefused, match="real socket sendmsg"):
            udp6.sendmsg([b"x"], [], 0, ("::1", 9, 0, 0))
    a, b = socket.socketpair()                                                      # an AF_UNIX pair stays allowed
    with a, b:
        a.sendmsg([b"ok"])
        assert b.recv(2) == b"ok"
    if "posix_spawn" in REAL_OS:
        with pytest.raises(conftest.NetworkOrProcessRefused, match=r"real posix_spawn \('/usr/bin/true'\)"):
            os.posix_spawn("/usr/bin/true", ["true"], {})
        with pytest.raises(conftest.NetworkOrProcessRefused, match=r"real posix_spawnp \('true'\)"):
            os.posix_spawnp("true", ["true"], {})


def test_g1_g4_the_kits_http_libraries_stop_in_the_guard_before_any_lookup(monkeypatch):
    """The two clients a kit file could reach: http.client (urllib's transport) and huggingface_hub's (requests over
    urllib3, when installed). Both stop in the guard before a name lookup or a packet: http.client at
    socket.create_connection, urllib3 at its lookup (G1). The lookups sit over sentinels (see above)."""
    import http.client
    _sentinels(monkeypatch)
    conn = http.client.HTTPSConnection("huggingface.co", timeout=1)
    with pytest.raises(conftest.NetworkOrProcessRefused, match="PP10"):
        conn.request("GET", "/api/whoami-v2", headers={"Authorization": "Bearer " + fake_token()})
    conn.close()
    urllib3 = pytest.importorskip("urllib3")
    pool = urllib3.HTTPSConnectionPool("huggingface.co", 443, retries=False, timeout=1)
    with pytest.raises(BaseException) as info:
        pool.request("GET", "/api/whoami-v2")
    chain, exc = [], info.value
    while exc is not None and len(chain) < 10:
        chain.append(exc)
        exc = exc.__cause__ or exc.__context__
    assert any(isinstance(e, conftest.NetworkOrProcessRefused) for e in chain), [type(e).__name__ for e in chain]
    assert not any(isinstance(e, AssertionError) for e in chain)
    pool.close()
