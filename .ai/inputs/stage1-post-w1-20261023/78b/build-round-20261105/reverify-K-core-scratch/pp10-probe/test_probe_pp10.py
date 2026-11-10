"""reverify-K-core: a scratch probe of the PP10 guard (tests/conftest.py, copied beside this file, autouse).

Each probe records whether the guard refused the call (NetworkOrProcessRefused), the call escaped the guard and
reached the operating system, or something else happened. Every address is loopback (127.0.0.1, a closed port) or
local, so nothing leaves this machine; every process started is a local one (/usr/bin/true, this interpreter, a
multiprocessing child that prints one word). The probe asserts nothing about the guard: it writes the outcomes to
probe-results.json beside this file and prints them, for the report.
"""
from __future__ import annotations

import json
import os
import pathlib
import socket
import subprocess
import sys
import urllib.request

import conftest

HERE = pathlib.Path(__file__).resolve().parent
RESULTS: dict[str, str] = {}


def outcome(name, fn):
    try:
        value = fn()
    except conftest.NetworkOrProcessRefused as exc:
        RESULTS[name] = f"REFUSED by the guard: {str(exc)[:70]}"
    except Exception as exc:                       # the call reached the OS and the OS answered
        RESULTS[name] = f"ESCAPED the guard; OS answered {type(exc).__name__}: {str(exc)[:60]}"
    else:
        RESULTS[name] = f"ESCAPED the guard; returned {value!r}"[:140]


def _udp_loopback():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        return s.sendto(b"x", ("127.0.0.1", 9))     # loopback discard port; no packet leaves the host
    finally:
        s.close()


def _raw_socket_connect():
    import _socket
    s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        return s.connect(("127.0.0.1", 9))          # a closed loopback port: ECONNREFUSED if the call reaches the OS
    finally:
        s.close()


def _fork_and_exit():
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    _, status = os.waitpid(pid, 0)
    return f"forked child {pid} exited with status {status}"


def _multiprocessing_spawn():
    import multiprocessing
    ctx = multiprocessing.get_context("spawn")
    p = ctx.Process(target=print, args=("probe child",))
    p.start()
    p.join(30)
    return f"multiprocessing spawn child exitcode {p.exitcode}"


def _http_client_loopback():
    import http.client
    c = http.client.HTTPConnection("127.0.0.1", 9, timeout=0.5)
    c.request("GET", "/")
    return c.getresponse().status


def test_probe_expected_refusals_and_possible_escapes(tmp_path):
    # Calls the guard documents as refused (they must be):
    outcome("A1 subprocess.run ssh", lambda: subprocess.run(["ssh", "-V"], capture_output=True))
    outcome("A2 socket.socket().connect loopback", lambda: socket.socket().connect(("127.0.0.1", 9)))
    outcome("A3 urlopen loopback", lambda: urllib.request.urlopen("http://127.0.0.1:9/", timeout=0.5))
    outcome("A4 http.client direct (create_connection)", _http_client_loopback)
    outcome("A5 os.system true", lambda: os.system("true"))
    outcome("A6 os.popen true", lambda: os.popen("true").read())
    outcome("A7 posix_spawn /usr/bin/true (message names which call?)",
            lambda: os.posix_spawn("/usr/bin/true", ["true"], {}))
    outcome("A8 the kit's interpreter without local_processes", lambda: subprocess.run([sys.executable, "-c", "pass"]))
    # Other ways out of the process (loopback or local only):
    outcome("B1 os.fork + os._exit (a real fork)", _fork_and_exit)
    outcome("B2 multiprocessing spawn (fork_exec, not Popen)", _multiprocessing_spawn)
    outcome("B3 os.spawnlp /usr/bin/true (fork+exec in os.py)", lambda: os.spawnlp(os.P_WAIT, "true", "true"))
    outcome("B4 _socket.socket().connect loopback (the C class, not socket.socket)", _raw_socket_connect)
    outcome("B5 UDP sendto loopback (no connect)", _udp_loopback)
    outcome("B6 socket.getaddrinfo localhost (resolver not patched; local name)", lambda: len(socket.getaddrinfo("localhost", 80)))
    (HERE / "probe-results.json").write_text(json.dumps(RESULTS, indent=1) + "\n")
    print(json.dumps(RESULTS, indent=1))


def test_probe_local_processes_permits_git_whole(local_processes):
    done = subprocess.run(["git", "--version"], capture_output=True, text=True)
    RESULTS["C1 git --version under local_processes"] = f"ESCAPED (permitted): exit {done.returncode}, {done.stdout.strip()[:40]}"
    (HERE / "probe-results.json").write_text(json.dumps(RESULTS, indent=1) + "\n")
    print(json.dumps({k: v for k, v in RESULTS.items() if k.startswith("C")}, indent=1))
