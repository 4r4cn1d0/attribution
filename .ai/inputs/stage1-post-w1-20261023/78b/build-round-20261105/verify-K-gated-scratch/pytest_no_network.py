"""Run pytest with every socket connection refused (verifier's M check that the gated tests open no network).

    PY -B pytest_no_network.py BASETEMP TEST_PATH [TEST_PATH ...]

Patches socket.socket.connect, socket.socket.connect_ex, socket.create_connection and socket.getaddrinfo to raise
before any pytest import. cwd must be the repository root the builders used (ws-k). Exit code is pytest's.
"""
import socket
import sys


class NetworkRefused(RuntimeError):
    pass


def _refuse(*a, **k):
    raise NetworkRefused("the verifier blocked every socket connection for this run")


socket.socket.connect = _refuse
socket.socket.connect_ex = _refuse
socket.create_connection = _refuse
socket.getaddrinfo = _refuse

import pytest  # noqa: E402

if __name__ == "__main__":
    basetemp, paths = sys.argv[1], sys.argv[2:]
    sys.exit(pytest.main(["-p", "no:cacheprovider", "-q", "-rfE", "--basetemp", basetemp, *paths]))
