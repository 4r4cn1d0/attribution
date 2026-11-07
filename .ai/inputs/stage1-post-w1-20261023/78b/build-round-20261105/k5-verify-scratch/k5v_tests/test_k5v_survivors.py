"""K5 re-verifier's scratch tests (not for merge as is; a ready form for the lead). Each one pins a gap that one of my
hand mutants showed: it passes on the fixer's tree and fails under its mutant. Every token-shaped value is built here
at test time and no file holding one stays after the test. Nothing here reaches the network: the real socket probes
use numeric non-loopback addresses only after the hook refuses the same event raised by hand (fail-closed), and the
HTTP test replaces http.client's connection classes by recorders (no socket)."""
from __future__ import annotations

import _thread
import email.message
import http.client
import importlib
import shutil
import socket
import ssl
import threading
import urllib.request

import pytest

import conftest
import test_pp10_process_wide as pw
from test_scorer_block_78b import (BASE_UNIT, hx, load_by_path, sc_plan, sha, so, unit_copy, unit_run,  # noqa: F401
                                   write)
from test_gated_78b import HUB, LLAMA_REPO, LLAMA_REV, fake_token, wl  # noqa: F401


# ---- V1 (D1): c0 refuses a packed source unit that is a symbolic link (K5v-D1c) ---------------------------------
def test_v1_c0_refuses_a_linked_source_unit_even_when_its_target_has_the_pinned_bytes(so, tmp_path):
    runner = load_by_path("jr78_k5v_v1", so.root / "setup" / "job_runner_stage1.py")
    good = {"kind": "COMPLETE (synthetic)", "checkpoints": {"e1": {"adapter_fingerprint": hx("the real e1")}}}
    rel = "inputs/source_complete-R-1101/COMPLETE.json"
    target = write(tmp_path / "elsewhere" / "COMPLETE.json", good)
    (tmp_path / rel).parent.mkdir(parents=True)
    (tmp_path / rel).symlink_to(target)
    pins = {"source_complete:R:1101": sha(target), "oext_bank": hx("ob"), "oext_record": hx("or")}
    inputs = {"source_complete:R:1101": rel, "oext_bank": "inputs/oext_bank/b.json",
              "oext_record": "inputs/oext_record/r.json"}
    doc = {"files": {inputs[n]: pins[n] for n in pins}, "inputs": inputs}
    job = {"kind": "c0", "arm": "R", "seed": 1101, "recipe": "B", "engine": "X", "inputs": pins,
           "edit": {"sha256": hx("rd1"), "path": "x"}, "expect_fingerprint": hx("the real e1")}
    with pytest.raises(runner.Unrunnable, match="is missing or differs from its pin"):
        runner.job_commands(sc_plan(so, job), "h", 0, tmp_path, {}, doc)


# ---- V2 (D3, S3a): a side unit with no e1 checkpoint at all is a crash (K5v-R21 variant) ----------------------------
def test_v2_a_side_unit_with_no_e1_checkpoint_is_a_crash(so, monkeypatch, tmp_path):
    side = unit_copy(BASE_UNIT)
    del side["checkpoints"]["e1"]
    rec, calls, root, runner = unit_run(so, monkeypatch, tmp_path, "o_only_with_regenerate", 0, side,
                                        {"complete": True, **unit_copy(BASE_UNIT)})
    assert rec["status"] == "crashed" and "no e1 adapter fingerprint" in rec["why"]


# ---- V3 (R1): the wrapper refuses a real socket made with an explicit protocol (K5v-G1-explicit-proto) -----------
def _explicit_proto_probes() -> dict:
    def call(family, kind, proto, method, *args):
        with socket.socket(family, kind, proto) as sock:
            return pw._only_if_the_hook_refuses("socket." + method, family, args[-1],
                                                lambda: getattr(sock, method)(*args))
    return {"udp-sendto-v4": pw._outcome(lambda: call(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP, "sendto",
                                                      b"x", ("203.0.113.9", 9))),
            "udp-sendto-v6": pw._outcome(lambda: call(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP, "sendto",
                                                      b"x", pw.V6)),
            "tcp-connect-v4": pw._outcome(lambda: call(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP,
                                                       "connect", ("203.0.113.9", 9)))}


AT_COLLECTION_PROTO = _explicit_proto_probes()


@pytest.fixture(scope="module")
def module_proto_probes():
    """Before any test's function-scoped pp10_guard (only the process-wide layer exists here), as the D1 test does."""
    return _explicit_proto_probes()


def test_v3_the_wrapper_refuses_real_sockets_made_with_an_explicit_protocol(module_proto_probes):
    for where, results in (("collection", AT_COLLECTION_PROTO), ("module fixture", module_proto_probes)):
        pw._all_refused(results.items(), where)
        assert all(pw.WRAP in text for _, text in results.values()), where


# ---- V4 (R2): the hook refuses in a default-named thread and in a _thread thread (K5v-G2 x2) ------------------------
def _in_default_thread(probe):
    box = {}
    worker = threading.Thread(target=lambda: box.update(result=probe()), daemon=True)     # no name: "Thread-N (...)"
    worker.start()
    worker.join(30)
    assert not worker.is_alive() and worker.name.startswith("Thread-")
    return box["result"]


def _in_raw_thread(probe):
    box, done = {}, threading.Event()

    def body():
        try:
            box["kind"] = type(threading.current_thread()).__name__
            box["result"] = probe()
        finally:
            done.set()
    _thread.start_new_thread(body, ())
    assert done.wait(30)
    assert box["kind"] == "_DummyThread"
    return box["result"]


EVENTS = pw.HOOK_EVENTS + pw.BYTES_EVENTS
AT_COLLECTION_DEFAULT = _in_default_thread(lambda: pw._hook_probes(EVENTS))
AT_COLLECTION_RAW = _in_raw_thread(lambda: pw._hook_probes(EVENTS))


def test_v4_the_hook_refuses_in_a_default_named_thread_and_in_a_raw_thread():
    pw._all_refused(AT_COLLECTION_DEFAULT, "collection default-named thread")
    pw._all_refused(AT_COLLECTION_RAW, "collection _thread thread")
    pw._all_refused(_in_default_thread(lambda: pw._hook_probes(EVENTS)), "test default-named thread")
    pw._all_refused(_in_raw_thread(lambda: pw._hook_probes(EVENTS)), "test _thread thread")


# ---- V5 (R3): a real 302 through the opener's whole dispatch never carries the token off the Hub (K5v-G3) ------------
CDN_HOST = "cdn-lfs.example.net"


class _Resp:
    def __init__(self, status: int, body: bytes = b"", location: str | None = None):
        self.status = self.code = status
        self.reason, self.body = "synthetic", body
        self.headers = email.message.Message()
        if location is not None:
            self.headers["Location"] = location
        self.sock = None

    def info(self):
        return self.headers

    def getcode(self):
        return self.status

    def read(self, limit=-1):
        return self.body if limit is None or limit < 0 else self.body[:limit]

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _whole_dispatch(monkeypatch, answers: dict):
    """build_opener replaced: the REAL opener, whose instance ``open`` runs the request processors, opener._open AND
    the response processors (HTTPErrorProcessor -> the redirect handler's http_error_30x -> parent.open again), i.e.
    OpenerDirector.open's steps without its audit event. http.client's connections are recorders (no socket): plain
    HTTP fails at once; each HTTPS connection records (host, verifying, Authorization sent) and answers by host."""
    real_build, sent = urllib.request.build_opener, []

    class PlainHTTP:
        def __init__(self, host, *a, **kw):
            raise AssertionError(f"plain HTTP to {host!r}")

    class RecordingHTTPS:
        def __init__(self, host, port=None, *, timeout=None, context=None, check_hostname=None, **kw):
            ctx = context if context is not None else ssl._create_default_https_context()
            verifying = ctx.verify_mode == ssl.CERT_REQUIRED and (ctx.check_hostname if check_hostname is None
                                                                  else check_hostname) is True
            self.host, self.verifying, self.sock = host, verifying, None

        def set_debuglevel(self, level):
            pass

        def set_tunnel(self, *a, **kw):
            raise AssertionError("a proxy tunnel")

        def request(self, method, url, body=None, headers=None, **kw):
            sent.append({"host": self.host, "verifying": self.verifying,
                         "authorization": any(k.lower() == "authorization" for k in (headers or {}))})

        def getresponse(self):
            return answers[self.host]()

        def close(self):
            pass

    monkeypatch.setattr(http.client, "HTTPConnection", PlainHTTP)
    monkeypatch.setattr(http.client, "HTTPSConnection", RecordingHTTPS)

    def build_opener(*handlers):
        opener = real_build(*handlers)

        def fake_open(request, data=None, timeout=None):
            request.timeout = timeout
            protocol = request.type
            for processor in opener.process_request.get(protocol, []):
                request = getattr(processor, protocol + "_request")(request)
            response = opener._open(request, request.data)
            for processor in opener.process_response.get(protocol, []):
                response = getattr(processor, protocol + "_response")(request, response)
            return response
        opener.open = fake_open
        return opener
    monkeypatch.setattr(urllib.request, "build_opener", build_opener)
    return sent


@pytest.mark.parametrize("code", (301, 302, 303, 307, 308))
def test_v5_a_redirect_off_the_hub_through_the_whole_dispatch_drops_the_token(wl, monkeypatch, code):
    launch = importlib.import_module("launch")
    token = fake_token()
    url = f"{HUB}/{LLAMA_REPO}/resolve/{LLAMA_REV}/config.json"
    sent = _whole_dispatch(monkeypatch, {
        "huggingface.co": lambda: _Resp(code, location=f"https://{CDN_HOST}/signed/blob?x=1"),
        CDN_HOST: lambda: _Resp(206, b"xyz")})
    assert launch.http_get(url, token, {"Range": "bytes=0-0"}) == (206, b"x")
    assert [(s["host"], s["authorization"]) for s in sent] == [("huggingface.co", True), (CDN_HOST, False)]
    assert all(s["verifying"] for s in sent)
