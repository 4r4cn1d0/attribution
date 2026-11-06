"""K3 of T4 step 2: the 7-8B kit's gated-token launch path (runkit/family-probe/launch.py:8-21 ported into launch.py;
the gated download live in setup/download_models_stage1.py for llama31-8b; the stdin hand-over through orchestrate.py
and host.py), plus the launch-path tests the stage-1 kit holds for launch.py, host.py and budget.py, ported to block 0
(the guard-off decision, the $10/h limit, the shared lock, the full-cap count, K6's exit code) and host.py pull-states
(KD5; the OLMo 3 kit's command, K2's job 1).

No network: urllib is replaced at launch.py's one boundary (``get``), ssh and the children by fakes, huggingface_hub by
a fake snapshot_download. Every token is FAKE: a string of the HF token's shape built at test time (rk.fake_token), never
a real one; no secrets file or token variable of the Mac is read (the tests set and delete their own). Every record,
log line, argument list and file the fakes see is searched for the fake token (and secret_scan runs over the trees).
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import importlib
import importlib.util
import io
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import tarfile
import types
import urllib.error
import urllib.request
from pathlib import Path

import pytest

import test_stage1_runkit as rk
from test_stage1_runkit import w, wf  # noqa: F401 - the 7-8B World fixtures (olmo2-7b; both families)

KIT = rk.KIT
STAGE1 = rk.STAGE1
write_json, sha, fake_token = rk.write_json, rk.sha, rk.fake_token
HUB = "https://huggingface.co"
LLAMA_REPO = "meta-llama/Llama-3.1-8B-Instruct"
LLAMA_REV = "0e9e39f249a16976918f6564b8830bc894c89659"
LLAMA_FILES = ["config.json", "generation_config.json", "model.safetensors.index.json",
               "model-00001-of-00004.safetensors", "model-00002-of-00004.safetensors",
               "model-00003-of-00004.safetensors", "model-00004-of-00004.safetensors",
               "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]
GUARD_REPO = "Qwen/Qwen3Guard-Gen-4B"
EXTRA_MODULES = ("orchestrate", "job_runner_stage1_for_orchestrate")


def host_of(w) -> str:
    return f"{w.family}-0-1"


def load_by_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def files_holding(root: Path, text: str) -> list[str]:
    """Every file under ``root`` whose bytes hold ``text`` (the direct search for the fake token)."""
    needle = text.encode()
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and not p.is_symlink()
                  and needle in p.read_bytes())


def no_token_in_env(env: dict, token: str) -> bool:
    return all(name not in env for name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")) and \
        not any(token in (v or "") for v in env.values())


@pytest.fixture(autouse=True)
def fresh_launch_modules():
    """orchestrate (and the runner it loads by path) are not in rk.MODULES: every test here starts and ends without a
    cached copy, so a World of the other family never sees a stale module."""
    for name in EXTRA_MODULES:
        sys.modules.pop(name, None)
    yield
    for name in EXTRA_MODULES:
        sys.modules.pop(name, None)


@pytest.fixture
def wl(tmp_path, monkeypatch):
    """A llama31-8b World (its sealed-set pin test-local, as K1's tests do) with block 0's plan written."""
    world = rk.World(tmp_path, monkeypatch, "llama31-8b")
    world.init()
    yield world
    for name in rk.MODULES:
        sys.modules.pop(name, None)


@pytest.fixture
def wo(w):
    """The olmo2-7b World with block 0's plan written."""
    w.init()
    return w


class FakeHub:
    """launch.py's ``get`` boundary: whoami-v2 answers (status, body); every file answers (range_status, b"x").
    Records every call (url, headers, limit) and the token each call carried."""

    def __init__(self, whoami=(200, None), ranges: dict | None = None, default_range: int = 206):
        self.whoami, self.ranges, self.default = whoami, ranges or {}, default_range
        self.calls, self.tokens = [], set()

    def __call__(self, url, token, headers=None, limit=1):
        self.calls.append((url, dict(headers or {}), limit))
        self.tokens.add(token)
        if url.endswith("/api/whoami-v2"):
            status, body = self.whoami
            if body is None:
                body = json.dumps({"auth": {"accessToken": {"role": "read", "fineGrained": {}}}}).encode()
            return status, body
        name = url.rsplit("/", 1)[-1]
        return self.ranges.get(name, self.default), b"x"


def whoami_body(role, scopes=()) -> bytes:
    return json.dumps({"auth": {"accessToken": {"role": role, "fineGrained": {"scoped": [{"permissions": list(scopes)}]}}},
                       "name": "synthetic-user"}).encode()


# ===== 1. the constants and the per-family gated entries ===========================================================
def test_the_token_variable_is_the_first_scrubbed_name_and_only_llamas_plan_is_gated(wf, monkeypatch):
    w = wf
    launch, orch = importlib.import_module("launch"), importlib.import_module("orchestrate")
    assert launch.HF_TOKEN_ENV == orch.HF_TOKEN_ENV == "HF_TOKEN" == w.rules.TOKEN_ENV_NAMES[0]
    assert w.rules.TOKEN_ENV_NAMES == ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
    entries = launch.gated_entries()
    assert entries == orch.gated_entries()
    if w.family == "llama31-8b":
        assert [(e["role"], e["repo_id"], e["revision"], e["gated"]) for e in entries] == [("policy", LLAMA_REPO, LLAMA_REV, True)]
        assert entries[0]["patterns"] == LLAMA_FILES                 # exact names: never original/consolidated.00.pth
    else:
        assert entries == []
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    env = launch.child_env()                                         # the detached orchestrate child's environment
    assert ("HF_TOKEN" in env) is (w.family == "llama31-8b")
    for module in (launch, orch, importlib.import_module("host")):
        assert no_token_in_env(module.clean_env(), token)            # every other child


# ===== 2. whoami-v2 and the Range check =============================================================================
def test_whoami_refuses_an_http_error_before_any_range_request_and_records_nothing(wl):
    launch = importlib.import_module("launch")
    token = fake_token()
    for status in (401, 403, 500):
        hub = FakeHub(whoami=(status, b""))
        with pytest.raises(SystemExit, match=f"whoami-v2 answered {status}: the token is not valid"):
            launch.gated_precheck(host_of(wl), env={"HF_TOKEN": token}, get=hub)
        assert len(hub.calls) == 1 and hub.calls[0][0] == f"{HUB}/api/whoami-v2" and hub.calls[0][2] == launch.WHOAMI_LIMIT
    hub = FakeHub(whoami=(launch.NO_REPLY, b"URLError: synthetic no reply"))     # D4: no reply is its own refusal
    with pytest.raises(SystemExit, match="whoami-v2 got no reply \\(URLError: synthetic no reply\\): the network or TLS"):
        launch.gated_precheck(host_of(wl), env={"HF_TOKEN": token}, get=hub)
    assert len(hub.calls) == 1
    assert not (wl.root / "hosts" / host_of(wl) / "token-check.json").exists()


@pytest.mark.parametrize("body", [b"not json at all", b"[1, 2, 3]", b'{"auth": "a string"}',
                                  b'{"auth": {"accessToken": [1]}}', b'{"type": "org", "name": "x"}', b"", b"null"])
def test_an_unreadable_or_oddly_shaped_whoami_reply_only_warns_and_the_range_check_decides(wl, body, capsys):
    """The family-probe kit's review fix 6 (the user waived the read-only precondition): the role is recorded as
    unknown with a token-scope-warning; every gated file must still answer 206, else the launch refuses."""
    launch = importlib.import_module("launch")
    token = fake_token()
    hub = FakeHub(whoami=(200, body))
    record = launch.gated_precheck(host_of(wl), env={"HF_TOKEN": token}, get=hub)
    assert record["role"] in ("unknown (whoami-v2 reply unreadable)", None)
    assert [x["event"] for x in record["warnings"]] == ["token-scope-warning"] and record["warnings"][0]["extra_scopes"] == []
    assert set(record["range_status"].values()) == {206} and len(record["range_status"]) == len(LLAMA_FILES)
    printed = capsys.readouterr().out.strip().splitlines()
    assert len(printed) == 1 and json.loads(printed[0])["event"] == "token-scope-warning" and token not in printed[0]
    hub = FakeHub(whoami=(200, body), ranges={"config.json": 403})
    with pytest.raises(SystemExit, match="gated access check failed"):
        launch.gated_precheck(host_of(wl), env={"HF_TOKEN": token}, get=hub)


@pytest.mark.parametrize("role, scopes, warned, extra", [
    ("read", (), False, []),
    ("fineGrained", ("repo.content.read", "user.billing.read"), False, []),
    ("fineGrained", ("repo.content.read", "repo.write", "inference.serverless.write"), True,
     ["inference.serverless.write", "repo.write"]),
    ("write", (), True, []),
    (None, (), True, [])])
def test_the_role_and_the_scope_names_are_recorded_and_a_write_role_or_scope_only_warns(wl, role, scopes, warned, extra,
                                                                                        capsys):
    launch = importlib.import_module("launch")
    token = fake_token()
    hub = FakeHub(whoami=(200, whoami_body(role, scopes)))
    record = launch.gated_precheck(host_of(wl), env={"HF_TOKEN": token}, get=hub)
    assert record["role"] == role and record["family"] == "llama31-8b" and record["host"] == host_of(wl)
    if warned:
        assert record["warnings"] == [{"event": "token-scope-warning", "role": role, "extra_scopes": extra}]
    else:
        assert record["warnings"] == []
    saved = json.loads((wl.root / "hosts" / host_of(wl) / "token-check.json").read_text())
    assert saved == record and set(saved) == {"utc", "family", "host", "role", "warnings", "range_status"}
    text = json.dumps(saved) + capsys.readouterr().out
    assert token not in text and "synthetic-user" not in text          # the reply's other fields are not kept either


def test_the_range_requests_cover_every_gated_file_at_the_pinned_revision_and_a_non_206_refuses(wl):
    launch = importlib.import_module("launch")
    token = fake_token()
    hub = FakeHub()
    record = launch.gated_precheck(host_of(wl), env={"HF_TOKEN": token}, get=hub)
    ranged = [(u, h) for u, h, limit in hub.calls if not u.endswith("whoami-v2")]
    assert [u for u, _ in ranged] == [f"{HUB}/{LLAMA_REPO}/resolve/{LLAMA_REV}/{n}" for n in LLAMA_FILES]
    assert all(h == {"Range": "bytes=0-0"} for _, h in ranged) and all(limit == 1 for u, _, limit in hub.calls[1:])
    assert record["range_status"] == {f"{LLAMA_REPO}/{n}": 206 for n in LLAMA_FILES} and hub.tokens == {token}
    for name, status in (("model-00003-of-00004.safetensors", 403), ("tokenizer.json", 200), ("config.json", 404)):
        hub = FakeHub(ranges={name: status})
        with pytest.raises(SystemExit, match=rf"gated access check failed \(status codes \{{'{LLAMA_REPO}/{name}': {status}\}}\)"):
            launch.token_checks(token, launch.gated_entries(), get=hub)
    empty = [{**launch.gated_entries()[0], "patterns": []}]
    with pytest.raises(SystemExit, match="status codes none"):
        launch.token_checks(token, empty, get=FakeHub())
    open_only = [{"role": "guard", "repo_id": GUARD_REPO, "revision": "a" * 40, "gated": False, "patterns": ["x.json"]}]
    with pytest.raises(SystemExit, match="status codes none"):           # an open entry gets no Range request
        launch.token_checks(token, open_only, get=FakeHub())


REDIRECT_CODES = (301, 302, 303, 307, 308)      # RV2-3: every code urllib follows (http_error_301 ... _308)


@pytest.mark.parametrize("code", REDIRECT_CODES)
def test_the_redirect_handler_drops_the_authorization_header_when_the_redirect_leaves_the_hub(wl, code):
    launch = importlib.import_module("launch")
    token = fake_token()
    handler = launch.SameHostAuthRedirect()
    for newurl, kept in ((f"{HUB}/{LLAMA_REPO}/resolve/{LLAMA_REV}/config.json?x=1", True),
                         ("https://cdn-lfs.example.net/signed/blob?token=abc", False),
                         ("https://cas-bridge.xethub.hf.co/x", False)):
        req = urllib.request.Request(f"{HUB}/{LLAMA_REPO}/resolve/{LLAMA_REV}/config.json",
                                     headers={"Authorization": "Bearer " + token, "Range": "bytes=0-0"})
        new = handler.redirect_request(req, None, code, "Redirect", {}, newurl)
        assert new is not None and new.full_url == newurl
        assert ("Authorization" in new.headers) is kept and new.headers.get("Range") == "bytes=0-0"


# ===== 3. launch.py end to end with fake children =====================================================================
def _launch(w, monkeypatch, hub, create_ok=True, hosts=None, popen_env=None):
    """launch.main for block 0's host with fake children (reconcile and the guard exit 0; host.py create writes
    pod.json when ``create_ok``), a fake clock and a recorded timeline. Returns the run calls, the popen calls, the log
    lines and the timeline of events (get, run, popen)."""
    launch = importlib.import_module("launch")
    hosts = list(hosts or [host_of(w)])
    clock = [1_000_000.0]
    monkeypatch.setattr(launch, "time", types.SimpleNamespace(time=lambda: clock[0]))
    ran, started, logged, timeline = [], [], [], []
    seen_get = hub.__call__

    def get(*a, **k):
        timeline.append("get")
        return seen_get(*a, **k)

    def run(args, **kwargs):
        timeline.append(("run", args[1:3], (w.root / "hosts" / hosts[0] / "token-check.json").exists()))
        ran.append((list(args), dict(kwargs.get("env") or {})))
        if args[1:3] == ["host.py", "create"]:
            if create_ok:
                write_json(w.root / "hosts" / args[3] / "pod.json", {"id": f"pod-{args[3]}"})
            return subprocess.CompletedProcess(args, 0 if create_ok else 1, "", "create refused (synthetic 409)")
        return subprocess.CompletedProcess(args, 0, '{"allowed": true}', "")

    def popen(args, **kwargs):
        timeline.append(("popen", args[3:6]))
        started.append((list(args), dict(kwargs.get("env") or {})))

    def sleep(seconds):
        clock[0] += seconds
    monkeypatch.setattr(launch, "log", lambda **f: logged.append(f))
    monkeypatch.setattr(launch, "http_get", get)                     # the one network boundary, resolved at the call
    code = launch.main(hosts, run=run, popen=popen, sleep=sleep)
    launch.kit_lock().close()                                        # the kit lock was released either way
    return code, ran, started, logged, timeline


def test_a_llama_launch_checks_the_token_before_any_create_scrubs_every_child_but_the_detached_orchestrate_and_forgets_it(
        wl, monkeypatch, capsys):
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    monkeypatch.setenv("RENAMED_COPY_OF_THE_TOKEN", token)            # a renamed variable is scrubbed too (its value)
    monkeypatch.setenv("HARMLESS", "kept")
    hub = FakeHub(whoami=(200, whoami_body("fineGrained", ("repo.content.read",))))
    code, ran, started, logged, timeline = _launch(wl, monkeypatch, hub)
    assert code == 0 and [f["event"] for f in logged] == ["created", "all hosts created"]
    # the precheck ran before any child: whoami and the ten Range requests, then token-check.json, then the children
    gets = [t for t in timeline if t == "get"]
    assert len(gets) == 1 + len(LLAMA_FILES) and timeline[:len(gets)] == gets
    assert all(t[2] for t in timeline if t[0] == "run"), "token-check.json must exist before the first child runs"
    assert [t[1] for t in timeline if t[0] == "run"] == [["host.py", "reconcile"], ["budget.py", "check"], ["host.py", "create"]]
    # every run child (reconcile, the guard, create) gets a scrubbed environment; the argument lists hold no token
    for args, env in ran:
        assert no_token_in_env(env, token) and env.get("HARMLESS") == "kept" and token not in json.dumps(args)
    # the detached orchestrate child keeps the environment (it hands the token over stdin); nothing else does
    assert [t for t in timeline if t[0] == "popen"] == [("popen", ["orchestrate.py", "after-create", host_of(wl)])]
    (args, env), = started
    assert args[:2] == ["caffeinate", "-i"] and env.get("HF_TOKEN") == token and token not in json.dumps(args)
    # when the loop ends the token is gone from this process's environment
    assert "HF_TOKEN" not in os.environ and "RENAMED_COPY_OF_THE_TOKEN" not in os.environ and os.environ["HARMLESS"] == "kept"
    # no record, log line or file holds the token; the scanner finds no secret in the working copy
    record = json.loads((wl.root / "hosts" / host_of(wl) / "token-check.json").read_text())
    assert record["role"] == "fineGrained" and record["warnings"] == [] and set(record["range_status"].values()) == {206}
    assert token not in json.dumps(logged) and token not in capsys.readouterr().out
    assert files_holding(wl.root, token) == [] and files_holding(wl.repo, token) == []
    scan = importlib.import_module("secret_scan").scan_tree(wl.root)
    assert scan["secret_hits"] == [] and scan["model_text_pattern_hits"] == []
    assert (wl.root / f"hosts-full-{host_of(wl)}.log").exists()


def test_a_llama_launch_without_the_token_variable_refuses_before_any_child_and_releases_the_lock(wl, monkeypatch):
    launch = importlib.import_module("launch")
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN", raising=False)
    ran = []
    hub = FakeHub()
    monkeypatch.setattr(launch, "http_get", hub)
    with pytest.raises(SystemExit, match="HF_TOKEN is not set: a gated family \\(llama31-8b\\) needs the HF token"):
        launch.main([host_of(wl)], run=lambda *a, **k: ran.append(a), popen=lambda *a, **k: ran.append(a), sleep=lambda s: None)
    assert ran == [] and hub.calls == [] and not (wl.root / "hosts" / host_of(wl) / "token-check.json").exists()
    launch.kit_lock().close()                                        # released by the finally
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", fake_token())       # the other name is not read: HF_TOKEN_ENV only
    with pytest.raises(SystemExit, match="HF_TOKEN is not set"):
        launch.gated_precheck(host_of(wl), get=hub)
    assert hub.calls == []


def test_an_olmo_launch_never_touches_the_gated_path_and_still_scrubs_its_children_and_itself(wo, monkeypatch, capsys):
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)

    class Never:
        calls = []

        def __call__(self, *a, **k):
            raise AssertionError("an open family must not call the Hub")
    hub = Never()
    launch = importlib.import_module("launch")
    assert launch.gated_precheck(host_of(wo), get=hub) is None and launch.gated_entries() == []
    code, ran, started, logged, timeline = _launch(wo, monkeypatch, hub)
    assert code == 0 and "get" not in timeline and not (wo.root / "hosts" / host_of(wo) / "token-check.json").exists()
    assert all(no_token_in_env(env, token) for _, env in ran) and len(ran) == 3
    (args, env), = started
    assert no_token_in_env(env, token) and args[3:5] == ["orchestrate.py", "after-create"]   # the open child is scrubbed too
    assert "HF_TOKEN" not in os.environ
    assert token not in capsys.readouterr().out and files_holding(wo.root, token) == []


def test_k6_launch_exits_non_zero_when_a_host_it_should_create_has_no_pod(wf, monkeypatch):
    """K6 (the stage-1 kit's round 31, cert runbook D7) on block 0's host, both families: every create refused for
    launch.py's 2 h (24 rounds, 300 s apart): exit 4 after the log line naming the host; a created host: exit 0, its
    after-create started, no such line. A host whose pod.json exists already: exit 0 and no create. For llama31-8b
    the token precheck runs once per main, before the loop."""
    w = wf
    w.init()
    monkeypatch.setenv("HF_TOKEN", fake_token())
    h = host_of(w)
    hub = FakeHub()
    code, ran, started, logged, timeline = _launch(w, monkeypatch, hub, create_ok=False)
    creates = [a[3] for a, _ in ran if a[1:3] == ["host.py", "create"]]
    assert code == 4 and creates == [h] * 24 and started == []
    assert logged[-1] == {"event": "hosts-not-created", "hosts": [h], "exit": 4}
    assert [f["event"] for f in logged].count("create-failed") == 24
    assert len(hub.calls) == ((1 + len(LLAMA_FILES)) if w.family == "llama31-8b" else 0)   # once, not per round
    monkeypatch.setenv("HF_TOKEN", fake_token())
    code, ran, started, logged, timeline = _launch(w, monkeypatch, hub, create_ok=True)
    creates = [a[3] for a, _ in ran if a[1:3] == ["host.py", "create"]]
    assert code == 0 and creates == [h] and [a[3:6] for a, _ in started] == [["orchestrate.py", "after-create", h]]
    assert [f["event"] for f in logged] == ["created", "all hosts created"]
    monkeypatch.setenv("HF_TOKEN", fake_token())
    code, ran, started, logged, timeline = _launch(w, monkeypatch, hub, create_ok=False)
    assert (code, [a for a, _ in ran], [f["event"] for f in logged]) == (0, [], ["all hosts created"])


def test_launch_refuses_a_wrong_cap_another_familys_plan_or_an_unknown_host_and_gives_no_child_a_token(wf, monkeypatch):
    w = wf
    w.init()
    launch = importlib.import_module("launch")
    plan = w.plan()
    launch.check_hosts(plan, [host_of(w)])
    bad = json.loads(json.dumps(plan))
    bad["hosts"][host_of(w)]["cap_hours"] = 1.5
    with pytest.raises(SystemExit, match="the plan's cap differs from the cap of its jobs"):
        launch.check_hosts(bad, [host_of(w)])
    for change in ({"family": w.other}, {"kit_block": "A"}):
        with pytest.raises(SystemExit, match="plan.json is not this working copy's"):
            launch.check_hosts({**plan, **change}, [host_of(w)])
    with pytest.raises(SystemExit, match="is not a host of plan.json"):
        launch.check_hosts(plan, [f"{w.other}-0-1"])
    with pytest.raises(SystemExit, match="give at least one host"):
        launch.main([], run=None, popen=None, sleep=None)
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    monkeypatch.setenv("SOMETHING_ELSE", token)
    assert no_token_in_env(launch.clean_env(), token) and "PATH" in launch.clean_env()


# ===== 4. the guard-off decision, the $10/h limit, the shared lock, the full cap (ported from the stage-1 kit) =========
def _guard_off(w, **change) -> tuple[str, str]:
    rec = {"kind": "stage1 user decision: budget guard off", "user_words": rk.USER_WORDS, "utc": "2026-10-25T12:00:00Z",
           "recorded_by": "test", **change}
    return w.record(rec)


class _StopLoop(Exception):
    pass


def _launch_round(w, monkeypatch, guard_exit: int) -> tuple[list, list]:
    """launch.py's create loop for block 0's host with fake children: reconcile ok, budget.py check exits ``guard_exit``
    with a balance line, host.py create writes pod.json. Returns (the children run, the log lines)."""
    launch = importlib.import_module("launch")
    plan = w.plan()
    ran, logged = [], []
    line = json.dumps({"balance": 3.21, "committed_upper_usd": 9.0, "new_pod_upper_usd": 15.73, "reserve_usd": 6.0,
                       "allowed": guard_exit == 0})

    def run(args, **kwargs):
        ran.append(args[1:3])
        assert "HF_TOKEN" not in (kwargs.get("env") or {})
        if args[1:3] == ["host.py", "create"]:
            write_json(w.root / "hosts" / args[3] / "pod.json", {"id": "pod-x"})
        out = line if args[1] == "budget.py" else ""
        return subprocess.CompletedProcess(args, guard_exit if args[1] == "budget.py" else 0, out, "")

    def sleep(seconds):
        raise _StopLoop()
    monkeypatch.setattr(launch, "log", lambda **f: logged.append(f))
    try:
        launch._create_all(plan, [host_of(w)], run, lambda *a, **k: None, sleep)
    except _StopLoop:
        pass
    return ran, logged


@pytest.mark.parametrize("recorded, guard_exit, created", [(False, 3, False), (False, 0, True), (False, 1, False),
                                                           (True, 3, True), (True, 0, True), (True, 1, False)])
def test_launch_goes_past_the_guards_refusal_only_with_the_users_recorded_decision(wo, monkeypatch, recorded, guard_exit,
                                                                                    created):
    """Without the record the guard is as before (a refusal, exit 3, stops the create); with it, a refusal is logged
    beside the decision and the create goes on; the guard's live-balance read must still succeed (any other exit
    refuses either way), and budget.py check runs before every create (the stage-1 kit's test, on block 0)."""
    w = wo
    h = w.tool.record_simple("guard_off", *_guard_off(w))["sha256"] if recorded else None
    ran, logged = _launch_round(w, monkeypatch, guard_exit)
    assert ["budget.py", "check"] in ran and ran.index(["budget.py", "check"]) < len(ran)
    assert (["host.py", "create"] in ran) is created
    events = [f.get("event") for f in logged]
    assert ("budget-guard-refused" in events) is (not created)
    off = [f for f in logged if f.get("event") == "budget-guard-off"]
    if recorded and created:
        assert off == [{"host": host_of(w), "event": "budget-guard-off", "guard_exit": guard_exit, "decision_sha256": h,
                        "detail": json.dumps({"balance": 3.21, "committed_upper_usd": 9.0, "new_pod_upper_usd": 15.73,
                                              "reserve_usd": 6.0, "allowed": guard_exit == 0})}]
    else:
        assert off == []


def _extend(w, monkeypatch, guard_exit: int):
    host = importlib.import_module("host")
    write_json(w.root / "hosts" / host_of(w) / "pod.json", {"id": "pod-x", "name": host.name_of(host_of(w)),
                                                            "cap_stop_utc": "2026-11-20T12:00:00+00:00"})
    monkeypatch.setattr(host, "ssh_base", lambda h: [])
    ran = []

    def runner(args, **kwargs):
        ran.append(args[1] if args[0] != "ssh" else "ssh")
        assert "HF_TOKEN" not in (kwargs.get("env") or {})
        if args[0] == "ssh":
            return subprocess.CompletedProcess(args, 0, json.dumps({"governs": True, "acknowledged": True, "lease": "l1",
                                                                    "stop_at_utc": "2026-11-21T00:00:00+00:00"}), "")
        return subprocess.CompletedProcess(args, guard_exit, '{"allowed": false}', "")
    return host, ran, runner


@pytest.mark.parametrize("recorded, guard_exit, extended", [(False, 3, False), (True, 3, True), (True, 1, False),
                                                            (False, 0, True)])
def test_extend_cap_goes_past_the_guards_refusal_only_with_the_users_recorded_decision(wo, monkeypatch, recorded,
                                                                                       guard_exit, extended):
    w = wo
    monkeypatch.setenv("HF_TOKEN", fake_token())
    h = w.tool.record_simple("guard_off", *_guard_off(w))["sha256"] if recorded else None
    host, ran, runner = _extend(w, monkeypatch, guard_exit)
    far = 400 * 24 * 3600                                            # past the recorded stop: the guard runs
    if not extended:
        with pytest.raises(SystemExit, match="the budget guard refused the extension"):
            host.extend_cap(host_of(w), far, runner=runner)
        assert ran[-1].endswith("budget.py") and "ssh" not in ran
        return
    out = host.extend_cap(host_of(w), far, runner=runner)
    assert ran[0].endswith("budget.py") and ran[-1] == "ssh"                 # the guard still runs first (the read)
    saved = json.loads((w.root / "hosts" / host_of(w) / "cap-override.json").read_text())
    if recorded:
        assert out["budget_guard"] == saved["budget_guard"] == "off" and out["decision_sha256"] == h
        assert out["guard_exit"] == guard_exit
    else:
        assert "budget_guard" not in out                                     # as before


ABSENT = object()


def _fake_pod_api(price, calls: list):
    def api(method, path, payload=None):
        calls.append((method, path, (payload or {}).get("name")))
        if (method, path) == ("GET", "/pods"):
            return 200, []
        if (method, path) == ("POST", "/pods"):
            pod = {"id": "pod-synthetic", "name": payload["name"], "desiredStatus": "RUNNING"}
            return 201, pod if price is ABSENT else {**pod, "costPerHr": price}
        if method == "POST" and path.endswith("/stop"):
            return 200, {}
        return 200, {"desiredStatus": "EXITED"}
    return api


@pytest.mark.parametrize("price, created", [(1.79, True), (10.0, True), (10.01, False), (float("nan"), False),
                                            (float("inf"), False), (None, False), (ABSENT, False), ("1.79", False),
                                            (True, False), (10 ** 400, False)])
def test_create_refuses_a_missing_non_finite_or_over_ten_dollar_price_and_names_the_78b_pod(wf, monkeypatch, price,
                                                                                            created):
    """The $10/h create-time limit, the stop timer settings at the host's cap and stop-never-delete, with the user's
    guard-off decision recorded (not part of the switch); the pod is named attribution-s78-<host> (rules_78b's prefix,
    never stage 1's or Gate B's); an integer too large for a float is refused cleanly (the OLMo 3 kit's fix)."""
    w = wf
    w.init()
    w.tool.record_simple("guard_off", *_guard_off(w))
    assert w.rules.guard_off_record(w.root) is not None
    host = importlib.import_module("host")
    assert host.MAX_PRICE == 10.0 and host.name_of(host_of(w)) == f"attribution-s78-{w.family}-0-1"
    assert host.price_allowed(10 ** 400) is False and host.price_allowed(10.0) is True and host.price_allowed(True) is False
    cap = w.plan()["hosts"][host_of(w)]["cap_hours"]
    seen = {}
    (w.root / "ssh").mkdir(exist_ok=True)
    (w.root / "ssh" / "key.pub").write_text("synthetic public key\n")
    monkeypatch.setenv("HF_TOKEN", fake_token())

    def timer_settings(args, **kwargs):
        seen["cap_minutes"] = args[args.index("--cap-minutes") + 1]
        seen["env_clean"] = "HF_TOKEN" not in kwargs["env"]
        out = Path(args[args.index("--out") + 1])
        out.write_text(json.dumps({"env": {"POD_TIMER_CAP_MINUTES": seen["cap_minutes"]}, "docker_start_cmd": ["bash"],
                                   "cap_stop_utc": "2026-11-20T20:00:00+00:00"}))
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(host, "subprocess", argparse.Namespace(run=timer_settings, DEVNULL=subprocess.DEVNULL))
    calls = []
    monkeypatch.setattr(host, "api", _fake_pod_api(price, calls))
    monkeypatch.setattr(host, "SLEEP", lambda s: None)
    if created:
        assert host.create(host_of(w))["id"] == "pod-synthetic"
    else:
        with pytest.raises(SystemExit, match=r"above \$10\.00/h"):
            host.create(host_of(w))
        assert ("POST", "/pods/pod-synthetic/stop", None) in calls
    assert seen["cap_minutes"] == str(int(cap * 60)) and seen["env_clean"]  # the in-pod stop timer at the cap
    assert not any(m == "DELETE" for m, _, _ in calls)                       # stop, never delete
    names = [c[2] for c in calls if c[:2] == ("POST", "/pods")]
    assert names == [f"attribution-s78-{w.family}-0-1"] and not any("s1-" in n or "gateb" in n for n in names)
    intent = json.loads((w.root / "hosts" / host_of(w) / "create-intent.json").read_text())
    assert "env" not in intent["request_without_env"] and "HF_TOKEN" not in intent["env_names"]


def test_the_guard_reads_every_kit_folder_beside_the_working_copy_and_shares_the_lock(wo):
    """budget.py is the stage-1 kit's byte for byte (KD7, C7): KITS_GLOB family-probe-* sees every 7-8B working copy
    (tmp/family-probe-s78-<family>-<block>) and the one lock file is beside the kits."""
    w = wo
    budget = importlib.import_module("budget")
    assert budget.KITS_GLOB == ("family-probe-*", "gate-b-olmo*", "stage1-olmo*")
    assert budget.LOCK_NAME == "family-probe-budget.lock" == w.r78.LOCK_NAME
    assert budget.RESERVE_USD == 6.0 and budget.PLANNING_PRICE == 1.85
    for name in ("family-probe-s78-llama31-8b-0", "gate-b-olmo", "stage1-olmo", "family-probe-x", "other-kit", "s78-elsewhere"):
        (w.root.parent / name).mkdir(exist_ok=True)
    found = {p.name for p in budget.kit_folders()}
    assert {"family-probe-s78-olmo2-7b-0", "family-probe-s78-llama31-8b-0", "gate-b-olmo", "stage1-olmo", "family-probe-x"} <= found
    assert not found & {"other-kit", "s78-elsewhere"}
    assert all(n.startswith(("family-probe-", "gate-b-olmo", "stage1-olmo")) for n in found)   # the World's fixture folder too
    with budget.lock():
        assert (w.root.parent / "family-probe-budget.lock").exists()
    assert (w.root / "budget.py").read_bytes() == (STAGE1 / "budget.py").read_bytes()   # byte-identical (K1's rule)
    text = (w.root / "budget.py").read_text()
    assert "def main() -> int:" in text and "RUNPOD_OPERATOR_API_KEY" in text and "HF_TOKEN" not in text


def test_the_guard_counts_the_new_pod_at_its_full_cap(wo, monkeypatch, capsys):
    """8.5 h x $1.85 = $15.725: with $21.725 free the pod leaves exactly the $6 reserve (allowed); $21.72 refuses."""
    budget = importlib.import_module("budget")
    for free, code in ((21.725, 0), (21.72, 3)):
        monkeypatch.setattr(budget, "projection", lambda free=free: {"balance": free, "committed_upper_usd": 0.0,
                                                                     "free_after_commitments_usd": free, "reserve_usd": 6.0})
        monkeypatch.setattr(sys, "argv", ["budget.py", "check", "8.5", "1.85"])
        assert budget.main() == code
        assert json.loads(capsys.readouterr().out)["new_pod_upper_usd"] == rk.cents(8.5 * 1.85)
    assert (wo.root / "budget-checks.jsonl").read_text().count("\n") == 2


# ===== 5. orchestrate.py: the gated step and the stdin hand-over =======================================================
def test_the_gated_step_runs_after_the_bootstrap_check_and_before_the_preflight(wf, monkeypatch):
    w = wf
    orch = importlib.import_module("orchestrate")
    order, steps = [], []

    def rec(name, result=None):
        def f(*a, **k):
            order.append(name)
            steps.append(step["name"])
            return result
        return f
    for name, result in (("check_plan", {}), ("w1_18_hold", None), ("wait_ssh", None), ("check", None), ("bootstrap", None),
                         ("wait_file", {}), ("fetch", {"ok": True}), ("bootstrap_check", {}), ("gated_download", None),
                         ("preflight", {"ok": True, "folder": "cuda-preflight-1"}), ("preflight_check", {}),
                         ("cap_gate", {"ok": True}), ("start_job", None)):
        monkeypatch.setattr(orch, name, rec(name, result))
    step = {"name": "start"}
    orch._after_create(host_of(w), step)
    assert order == ["check_plan", "w1_18_hold", "wait_ssh", "check", "bootstrap", "wait_file", "fetch", "bootstrap_check",
                     "gated_download", "preflight", "fetch", "preflight_check", "cap_gate", "start_job"]
    assert steps[order.index("gated_download")] == "gated-download" and steps[order.index("preflight")] == "preflight"
    assert steps[order.index("bootstrap_check")] == "bootstrap-check" and step["name"] == "start-job"


def _orch_with_fake_host_tool(orch, monkeypatch, record_ok=True, tool_exit=0, write_record=True):
    """orchestrate.tool's subprocess.run replaced: records the argument list, the stdin text and the environment, and
    plays host.py gated-download (writes hosts/HOST/gated-download.json) when asked."""
    seen = []

    def run(args, **kwargs):
        seen.append({"args": list(args), "input": kwargs.get("input"), "env": dict(kwargs.get("env") or {})})
        if args[2:3] == ["gated-download"] and write_record:
            write_json(orch.HERE / "hosts" / args[3] / "gated-download.json",
                       {"utc": "2026-11-20T12:00:00+00:00", "ok": record_ok, "exit": 0 if record_ok else 1, "attempt": "20261120T120000Z"})
        return subprocess.CompletedProcess(args, tool_exit, "", "")
    monkeypatch.setattr(orch, "subprocess", types.SimpleNamespace(run=run, CompletedProcess=subprocess.CompletedProcess,
                                                                  STDOUT=subprocess.STDOUT, DEVNULL=subprocess.DEVNULL))
    return seen


def test_orchestrate_hands_the_token_to_host_py_over_stdin_in_a_scrubbed_environment_then_forgets_it(wl, monkeypatch):
    orch = importlib.import_module("orchestrate")
    h = host_of(wl)
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    monkeypatch.setenv("RENAMED_COPY_OF_THE_TOKEN", token)
    write_json(wl.root / "hosts" / h / "gated-download.json", {"ok": True, "exit": 0, "attempt": "stale"})   # archived first
    seen = _orch_with_fake_host_tool(orch, monkeypatch)
    orch.gated_download(h)
    (call,) = seen
    assert call["args"][1:] == [str(wl.root / "host.py"), "gated-download", h]      # no token in the argument list
    assert call["input"] == token + "\n"                                          # the one hand-over: stdin
    assert no_token_in_env(call["env"], token)                                    # host.py's environment is scrubbed
    assert "HF_TOKEN" not in os.environ and "RENAMED_COPY_OF_THE_TOKEN" not in os.environ   # forgotten after use
    log = [json.loads(x) for x in (wl.root / "hosts" / h / "orchestrate.jsonl").read_text().splitlines()]
    assert [x["event"] for x in log] == ["gated-download-finished"] and log[0]["ok"] is True and log[0]["tool_exit"] == 0
    earlier = list((wl.root / "hosts" / h).glob("gated-download-earlier-*.json"))
    assert len(earlier) == 1 and json.loads(earlier[0].read_text())["attempt"] == "stale"
    assert json.loads((wl.root / "hosts" / h / "gated-download.json").read_text())["attempt"] == "20261120T120000Z"
    assert files_holding(wl.root, token) == []
    # the failure paths: the record says ok false; host.py exits non-zero; no record written; no token variable
    for kwargs, match in (({"record_ok": False}, "the gated download failed"), ({"tool_exit": 1}, "the gated download failed"),
                          ({"write_record": False}, "the gated download failed")):
        monkeypatch.setenv("HF_TOKEN", token)
        _orch_with_fake_host_tool(orch, monkeypatch, **kwargs)
        with pytest.raises(SystemExit, match=match):
            orch.gated_download(h)
        assert "HF_TOKEN" not in os.environ                                       # scrubbed before the refusal
    monkeypatch.delenv("HF_TOKEN", raising=False)
    seen = _orch_with_fake_host_tool(orch, monkeypatch)
    with pytest.raises(SystemExit, match="HF_TOKEN is not set for the gated download"):
        orch.gated_download(h)
    assert seen == []


def test_orchestrate_on_olmo_never_reads_the_token_and_scrubs_its_own_environment(wo, monkeypatch):
    orch = importlib.import_module("orchestrate")
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    seen = _orch_with_fake_host_tool(orch, monkeypatch)
    assert orch.gated_download(host_of(wo)) is None and seen == []
    assert "HF_TOKEN" not in os.environ and not (wo.root / "hosts" / host_of(wo)).exists()


# ===== 6. host.py: the gated download over ssh's stdin; pull-states ====================================================
def test_host_gated_download_writes_the_token_to_ssh_stdin_only_and_records_no_secret(wl, monkeypatch, capsys):
    host = importlib.import_module("host")
    h = host_of(wl)
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    monkeypatch.setattr(host, "ssh_base", lambda hh: ["-p", "22", "root@203.0.113.9"])
    seen = []

    def runner(args, **kwargs):
        seen.append({"args": list(args), "input": kwargs.get("input"), "env": dict(kwargs.get("env") or {})})
        return subprocess.CompletedProcess(args, 0, "{}", "")
    record = host.gated_download(h, token, runner=runner)
    (call,) = seen
    assert call["args"][:4] == ["ssh", "-p", "22", "root@203.0.113.9"] and len(call["args"]) == 5
    command = call["args"][4]
    assert command.startswith(f"cd {host.REMOTE_ROOT} && python3 process_receipt.py --out gated-download-")
    assert command.endswith("-- venv/bin/python download_models_stage1.py --gated --token-stdin")
    assert token not in json.dumps(call["args"]) and call["input"] == token + "\n" and no_token_in_env(call["env"], token)
    assert record["ok"] is True and record["exit"] == 0 and set(record) == {"utc", "ok", "exit", "attempt"}
    assert command.split("gated-download-")[1].split(" ")[0] == record["attempt"]
    saved = json.loads((wl.root / "hosts" / h / "gated-download.json").read_text())
    assert saved == record and token not in json.dumps(saved)
    with pytest.raises(SystemExit, match="no token on stdin"):
        host.gated_download(h, "", runner=runner)
    with pytest.raises(ValueError, match="bad stamp"):
        host.gated_command("2026-11-20 12:00; rm -rf /")
    # the CLI reads the token from stdin, never from an argument, and prints the record only
    monkeypatch.setattr(host, "subprocess", types.SimpleNamespace(run=runner, DEVNULL=subprocess.DEVNULL))
    monkeypatch.setattr(sys, "argv", ["host.py", "gated-download", h])
    monkeypatch.setattr(sys, "stdin", io.StringIO(token + "\n"))
    assert host.main() == 0
    out = capsys.readouterr().out
    assert json.loads(out)["ok"] is True and token not in out and seen[-1]["input"] == token + "\n"
    assert files_holding(wl.root, token) == []
    assert "gated-download-*" in host.PULL_ITEMS and "gated-download-receipt.json" in host.PULL_ITEMS


def _tar_bytes(members: dict) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def test_pull_states_keeps_only_an_archive_that_holds_a_file_and_records_it(wo, monkeypatch, capsys):
    """KD5 (the OLMo 3 kit's command, K2's job 1): the tar of round1/*/states/e1 is kept with a pulls.jsonl line and one
    printed JSON record; an empty archive (GNU tar's zero blocks for an empty -T list), a failed ssh and an unknown
    checkpoint keep nothing."""
    host = importlib.import_module("host")
    h = host_of(wo)
    monkeypatch.setattr(host, "ssh_base", lambda hh: [])
    assert host.STATE_CHECKPOINTS == ("init", "q", "e1") and "pull-states" in host.__doc__
    payloads = {}

    def run(args, **kwargs):
        assert args[0] == "ssh" and "round1/*/states/e1" in args[-1] and "tar -cf - -T -" in args[-1]
        kwargs["stdout"].write(payloads["data"])
        return subprocess.CompletedProcess(args, payloads.get("code", 0))
    monkeypatch.setattr(host, "subprocess", types.SimpleNamespace(run=run, DEVNULL=subprocess.DEVNULL))
    payloads.update(data=_tar_bytes({"round1/1101-edit-x-e1-a1/states/e1/adapter.safetensors": b"A" * 64,
                                     "round1/1101-edit-x-e1-a1/states/e1/state.json": b'{"s": 1}'}))
    assert host.pull_states(h, "e1") == 0
    (final,) = list((wo.root / "retrieved" / h).glob("states-e1-*.tar"))
    printed = json.loads(capsys.readouterr().out)
    assert printed == {"file": final.name, "bytes": final.stat().st_size, "sha256": sha(final)}
    (line,) = [json.loads(x) for x in (wo.root / "retrieved" / h / "pulls.jsonl").read_text().splitlines()]
    assert {k: line[k] for k in ("file", "bytes", "sha256", "kind")} == {**printed, "kind": "states e1"}
    assert host.tar_file_count(final) == 2
    payloads.update(data=b"\0" * 10240)                              # an empty -T list: zero blocks, no file
    assert host.pull_states(h, "e1") == 1 and "refused" in capsys.readouterr().err
    payloads.update(data=b"", code=255)                              # ssh failed
    assert host.pull_states(h, "e1") == 255
    payloads.update(data=b"not a tar", code=0)
    assert host.pull_states(h, "e1") == 1 and host.tar_file_count(wo.root / "plan.json") == -1
    assert {p.name for p in (wo.root / "retrieved" / h).iterdir()} == {final.name, "pulls.jsonl"}   # nothing else kept
    with pytest.raises(SystemExit, match="checkpoint must be one of init, q, e1"):
        host.pull_states(h, "e2")
    monkeypatch.setattr(sys, "argv", ["host.py", "pull-states", h, "e1"])
    payloads.update(data=_tar_bytes({"round1/u/states/e1/f": b"x"}), code=0)
    assert host.main() == 0 and len(list((wo.root / "retrieved" / h).glob("states-e1-*.tar"))) in (1, 2)


# ===== 7. setup/download_models_stage1.py: the gated run live for llama31-8b, open with token=False for olmo2-7b =========
class FakeHubCache:
    """huggingface_hub.snapshot_download replaced: records every call's keyword arguments and lays the files out as the
    HF cache does (blobs/<sha256> with symlinks under snapshots/<revision>/)."""

    def __init__(self, hub: Path, contents: dict | None = None):
        self.hub, self.contents, self.calls = hub, contents or {}, []

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))
        repo = self.hub / f"models--{kwargs['repo_id'].replace('/', '--')}"
        snapshot = repo / "snapshots" / kwargs["revision"]
        (repo / "blobs").mkdir(parents=True, exist_ok=True)
        snapshot.mkdir(parents=True, exist_ok=True)
        names = [p for p in kwargs["allow_patterns"] if "*" not in p]
        if any("*" in p for p in kwargs["allow_patterns"]):          # an open repository's globs: one weights file
            names += ["config.json", "model.safetensors"]
        for name in names:
            data = self.contents.get((kwargs["repo_id"], name), f"{kwargs['repo_id']} {name} synthetic bytes".encode())
            digest = hashlib.sha256(data).hexdigest()
            blob = repo / "blobs" / (digest if name.endswith(".safetensors") else f"git-{digest[:12]}")
            blob.write_bytes(data)
            link = snapshot / name
            if not link.exists():
                link.symlink_to(os.path.relpath(blob, link.parent))
        return str(snapshot)


HF_PATH_VARS = ("HF_HOME", "XDG_CACHE_HOME", "HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE", "HF_TOKEN_PATH",
                "HUGGINGFACE_CO_STAGING", "HF_ENDPOINT")


def _download_world(tmp_path, monkeypatch, family: str, env: dict | None = None):
    """The pod's run folder (cwd) with probe.json for the family (the kit's download plan; weight pins equal to the
    fake policy files' digests), HOME under tmp_path, no token variable, none of the library's path variables but
    ``env`` (default: HF_HUB_CACHE under HOME); the fake cache is laid out where the script resolves hf_cache()."""
    probes = load_by_path("probes_k3", KIT / "probes.py")
    dl = load_by_path("download_models_k3", KIT / "setup" / "download_models_stage1.py")
    home, run = tmp_path / "home", tmp_path / "run"
    run.mkdir()
    monkeypatch.setenv("HOME", str(home))
    for name in HF_PATH_VARS + dl.TOKEN_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    for name, value in ({"HF_HUB_CACHE": str(home / ".cache" / "huggingface" / "hub")} if env is None else env).items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(run)
    plan = probes.stage1_download_plan(family)
    weights = {}
    for entry in plan:
        if entry["role"] == "policy":          # exact names (Llama) or the fake's one file for a glob (OLMo's *.safetensors)
            exact = [p for p in entry["patterns"] if p.endswith(".safetensors") and "*" not in p]
            for name in exact or ["model.safetensors"]:
                data = f"{family} {name} weights".encode()
                weights[(entry["repo_id"], name)] = data
    pins = sorted(hashlib.sha256(d).hexdigest() for d in weights.values())
    write_json(run / "probe.json", {"probe": family, "family": family, "plan": plan, "weight_pins": pins})
    fake = FakeHubCache(dl.hf_cache(), weights)
    monkeypatch.setattr(dl, "snapshot_download", fake)
    return dl, fake, run, home


def test_the_gated_run_passes_the_token_to_snapshot_download_only_and_writes_a_receipt_without_it(tmp_path, monkeypatch, capsys):
    dl, fake, run, home = _download_world(tmp_path, monkeypatch, "llama31-8b")
    token = fake_token()
    assert dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n")) == 0
    (call,) = fake.calls                                              # the gated policy only; the open guard is not touched
    assert call["repo_id"] == LLAMA_REPO and call["revision"] == LLAMA_REV and call["allow_patterns"] == LLAMA_FILES
    assert call["token"] == token and call["endpoint"] == HUB
    receipt = json.loads((run / "gated-download-receipt.json").read_text())
    assert receipt["ok"] is True and receipt["gated"] is True and receipt["token_source"] == "stdin"
    assert receipt["gated_repos"] == [LLAMA_REPO] and receipt["endpoint"] == HUB and receipt["cache_token_pattern_count"] == 0
    assert sorted(receipt["models"]) == ["policy"] and sorted(receipt["models"]["policy"]["files"]) == sorted(LLAMA_FILES)
    assert receipt["models"]["policy"]["snapshot"].endswith(LLAMA_REV)
    printed = capsys.readouterr().out
    assert json.loads(printed.strip().splitlines()[-1]) == {"ok": True, "gated": True, "models": ["policy"]}
    assert token not in printed and token not in json.dumps(receipt)
    assert files_holding(tmp_path, token) == [] and not (home / ".cache" / "huggingface" / "token").exists()
    assert not any(os.environ.get(n) for n in dl.TOKEN_ENV_NAMES) and os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] == "1"
    scan = load_by_path("secret_scan_k3", KIT / "secret_scan.py").scan_tree(tmp_path)
    assert scan["secret_hits"] == [] and scan["model_text_pattern_hits"] == []
    # the preflight's reading of the receipt (K2's gated_ready) finds every file in the cache
    pf = load_by_path("preflight_k3", KIT / "setup" / "preflight_stage1.py")
    pf.gated_ready(json.loads((run / "probe.json").read_text()), run)


def test_the_open_run_on_llama_downloads_the_guard_only_with_token_false_and_never_the_policy(tmp_path, monkeypatch, capsys):
    dl, fake, run, home = _download_world(tmp_path, monkeypatch, "llama31-8b")
    assert dl.main([]) == 0
    (call,) = fake.calls
    assert call["repo_id"] == GUARD_REPO and call["token"] is False and call["endpoint"] == HUB
    receipt = json.loads((run / "model-download-receipt.json").read_text())
    assert receipt["ok"] is True and receipt["gated"] is False and receipt["token_source"] is None and receipt["gated_repos"] == []
    assert sorted(receipt["models"]) == ["guard"] and not (run / "gated-download-receipt.json").exists()
    pf = load_by_path("preflight_k3b", KIT / "setup" / "preflight_stage1.py")
    with pytest.raises(SystemExit, match="a gated probe needs gated-download-receipt.json with ok true"):
        pf.gated_ready(json.loads((run / "probe.json").read_text()), run)      # the preflight waits for the gated step


def test_the_olmo_run_is_open_for_every_repository_and_its_gated_run_refuses(tmp_path, monkeypatch):
    dl, fake, run, home = _download_world(tmp_path, monkeypatch, "olmo2-7b")
    assert dl.main([]) == 0
    assert [(c["repo_id"], c["token"]) for c in fake.calls] == [("allenai/OLMo-2-1124-7B-Instruct", False),
                                                                ("allenai/OLMo-2-0425-1B-Instruct", False), (GUARD_REPO, False)]
    receipt = json.loads((run / "model-download-receipt.json").read_text())
    assert sorted(receipt["models"]) == ["audit_tokenizer", "guard", "policy"] and receipt["ok"] is True
    before = len(fake.calls)
    with pytest.raises(SystemExit, match="no gated repository in the plan: this family's downloads are open"):
        dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(fake_token() + "\n"))
    assert len(fake.calls) == before and not (run / "gated-download-receipt.json").exists()


def test_the_gated_run_refuses_a_set_token_variable_a_missing_token_a_bad_flag_pair_or_another_endpoint(tmp_path, monkeypatch):
    dl, fake, run, home = _download_world(tmp_path, monkeypatch, "llama31-8b")
    token = fake_token()
    with pytest.raises(SystemExit, match="--gated and --token-stdin go together"):
        dl.main(["--gated"], stdin=io.StringIO(token + "\n"))
    with pytest.raises(SystemExit, match="--gated and --token-stdin go together"):
        dl.main(["--token-stdin"], stdin=io.StringIO(token + "\n"))
    assert dl.TOKEN_ENV_NAMES == ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
    for name in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):             # RV2-4: hardcoded, not the list under test
        monkeypatch.setenv(name, token)
        stdin = io.StringIO(token + "\n")
        with pytest.raises(SystemExit, match=f"a token variable is set: \\['{name}'\\]"):
            dl.main(["--gated", "--token-stdin"], stdin=stdin)
        assert stdin.tell() == 0                                      # refused before the token is read
        monkeypatch.delenv(name)
    with pytest.raises(SystemExit, match="no token on stdin"):
        dl.main(["--gated", "--token-stdin"], stdin=io.StringIO("\n"))
    monkeypatch.setenv("HF_ENDPOINT", "https://hub.example.net")
    with pytest.raises(SystemExit, match="HF_ENDPOINT points elsewhere"):
        dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n"))
    monkeypatch.delenv("HF_ENDPOINT")
    (home / ".cache" / "huggingface").mkdir(parents=True)
    (home / ".cache" / "huggingface" / "token").write_text("a stored login (synthetic)\n")
    with pytest.raises(SystemExit, match="a stored HF login exists: .*/.cache/huggingface/token "):
        dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n"))
    assert fake.calls == [] and not list(run.glob("*receipt*"))


def test_a_wrong_weight_pin_a_blob_mismatch_or_a_token_pattern_in_the_cache_refuses_with_ok_false(tmp_path, monkeypatch):
    dl, fake, run, home = _download_world(tmp_path, monkeypatch, "llama31-8b")
    token = fake_token()
    probe = json.loads((run / "probe.json").read_text())
    write_json(run / "probe.json", {**probe, "weight_pins": ["0" * 64] * 4})
    with pytest.raises(SystemExit, match="differ from the pinned SHA-256 values"):
        dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n"))
    receipt = json.loads((run / "gated-download-receipt.json").read_text())
    assert receipt["ok"] is False and "models" not in receipt and token not in json.dumps(receipt)
    write_json(run / "probe.json", probe)
    # a token pattern (another synthetic string of the shape, not the fake token) in a non-blob cache file
    hub = home / ".cache" / "huggingface" / "hub"
    hub.mkdir(parents=True, exist_ok=True)
    (hub / "notes.txt").write_text("a leak would look like hf_" + "Q" * 40 + "\n")
    with pytest.raises(SystemExit, match="a token pattern is in the HF cache's non-blob files"):
        dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n"))
    receipt = json.loads((run / "gated-download-receipt.json").read_text())
    assert receipt["ok"] is False and receipt["cache_token_pattern_count"] == 1 and token not in json.dumps(receipt)
    (hub / "notes.txt").unlink()
    # a safetensors file whose blob name is not its SHA-256
    broken = FakeHubCache(hub, {})
    original = broken.__call__

    def tampered(**kwargs):
        snapshot = Path(original(**kwargs))
        link = snapshot / "model-00001-of-00004.safetensors"
        link.unlink()
        link.write_bytes(b"plain file, no blob")                     # resolve().name is the file name, not a digest
        return str(snapshot)
    monkeypatch.setattr(dl, "snapshot_download", tampered)
    with pytest.raises(SystemExit, match="the SHA-256 differs from its blob name"):
        dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n"))
    assert files_holding(tmp_path, token) == []


# ===== 8. the copied modules this stage adapted hold no secret and keep the pod-side script list ===================
def test_the_launch_path_files_hold_no_secret_and_the_pack_ships_the_gated_scripts(wf):
    w = wf
    scan = importlib.import_module("secret_scan")
    paths = [w.root / n for n in ("launch.py", "host.py", "orchestrate.py", "secret_scan.py", "setup/download_models_stage1.py",
                                  "setup/setup_and_fetch_stage1.sh", "setup/bootstrap_hr.sh")]
    assert scan.scan_paths(paths) == [] and all(p.is_file() for p in paths)
    pack = importlib.import_module("pack_setup")
    assert {"download_models_stage1.py", "setup_and_fetch_stage1.sh", "bootstrap_hr.sh"} <= set(pack.SETUP_FILES)
    bootstrap = pack.worker_bootstrap("X", "bundle.tar.gz", "b" * 64, "c" * 64, {}, None)
    assert "No token here" in bootstrap and "HF_TOKEN" not in bootstrap and "--gated" not in bootstrap
    fetch = (w.root / "setup" / "setup_and_fetch_stage1.sh").read_text()
    assert 'download_models_stage1.py "$@"' in fetch and "--gated" not in fetch.split("\n")[-3]
    assert (w.root / "setup" / "bootstrap_hr.sh").read_bytes() == (STAGE1 / "setup" / "bootstrap_hr.sh").read_bytes()
    assert (w.root / "secret_scan.py").read_bytes() == (STAGE1 / "secret_scan.py").read_bytes()


# ===== 9. fix-K-gated (verify-K-gated D1, D2, D4, D5, D6): http_get's own wiring, no-reply refusals, the =============
# after-download check, the library's cache and token paths. D3 stays as built (PP9).
class FakeResponse:
    def __init__(self, status: int, body: bytes):
        self.status, self.body = status, body

    def read(self, limit=-1):
        return self.body if limit is None or limit < 0 else self.body[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _real_opener_with_fake_open(monkeypatch, outcomes):
    """urllib.request.build_opener replaced by a recorder: it builds the REAL OpenerDirector with the handlers
    http_get passes (so the opener's handler list can be inspected), then shadows that one instance's ``open`` with a
    fake that records the request and the timeout and answers from ``outcomes`` in order (a (status, body) pair, or an
    exception to raise; the last outcome repeats). The class method OpenerDirector.open, which PP10's guard refuses,
    is never reached. Returns (the handler lists built, the opener instances, the (request, timeout) pairs opened)."""
    real_build = urllib.request.build_opener
    built, openers, opened, queue = [], [], [], list(outcomes)

    def build_opener(*handlers):
        built.append(list(handlers))
        opener = real_build(*handlers)

        def fake_open(request, timeout=None):
            opened.append((request, timeout))
            outcome = queue.pop(0) if len(queue) > 1 else queue[0]
            if isinstance(outcome, BaseException):
                raise outcome
            return FakeResponse(*outcome)
        opener.open = fake_open
        openers.append(opener)
        return opener
    monkeypatch.setattr(urllib.request, "build_opener", build_opener)
    return built, openers, opened


def test_d1_http_get_builds_its_opener_with_the_same_origin_redirect_handler_and_the_precheck_runs_through_it(wl, monkeypatch):
    launch = importlib.import_module("launch")
    token = fake_token()
    url = f"{HUB}/{LLAMA_REPO}/resolve/{LLAMA_REV}/config.json"
    built, openers, opened = _real_opener_with_fake_open(monkeypatch, [(206, b"xyz")])
    assert launch.http_get(url, token, {"Range": "bytes=0-0"}) == (206, b"x")           # the first ``limit`` bytes
    assert built == [[launch.SameHostAuthRedirect]]                                     # the one handler, by class
    (request, timeout), = opened
    assert request.full_url == url and timeout == launch.HTTP_TIMEOUT_S == 60
    assert request.get_header("Authorization") == "Bearer " + token and request.get_header("Range") == "bytes=0-0"
    kinds = [type(h) for h in openers[0].handlers]                                      # the real opener's handler list
    assert launch.SameHostAuthRedirect in kinds and urllib.request.HTTPRedirectHandler not in kinds
    # an HTTP error is its status with no body
    built, openers, opened = _real_opener_with_fake_open(monkeypatch, [urllib.error.HTTPError(url, 401, "Unauthorized", {}, None)])
    assert launch.http_get(url, token) == (401, b"") and built == [[launch.SameHostAuthRedirect]]
    # the precheck with no fake ``get``: token_checks runs the real http_get for whoami and the ten Range requests
    built, openers, opened = _real_opener_with_fake_open(monkeypatch, [(200, whoami_body("read")), (206, b"x")])
    record = launch.gated_precheck(host_of(wl), env={"HF_TOKEN": token})
    assert len(opened) == 1 + len(LLAMA_FILES) and len(built) == len(opened)
    assert [r.full_url for r, _ in opened] == [f"{HUB}/api/whoami-v2"] + [f"{HUB}/{LLAMA_REPO}/resolve/{LLAMA_REV}/{n}" for n in LLAMA_FILES]
    assert all(r.get_header("Authorization") == "Bearer " + token and t == 60 for r, t in opened)
    assert all(hs == [launch.SameHostAuthRedirect] for hs in built)
    assert record["role"] == "read" and set(record["range_status"].values()) == {206}
    written = (wl.root / "hosts" / host_of(wl) / "token-check.json").read_text()
    assert token not in written and "synthetic-user" not in written


def _no_fragment(text: str, token: str) -> bool:
    """RV2-2: no part of the token that a reader could use: the whole value, the value without its constant hf_ prefix
    (which the HF pattern and secret_scan do not see), and either half."""
    return all(part not in text for part in (token, token[3:], token[:20], token[20:]))


NO_REPLY_FAILURES = [
    ("dns", lambda t: urllib.error.URLError(socket.gaierror(8, "nodename nor servname provided, or not known"))),
    ("refused", lambda t: urllib.error.URLError(ConnectionRefusedError(61, "Connection refused"))),
    ("timeout", lambda t: TimeoutError("timed out")),                   # socket.timeout is TimeoutError (3.10+)
    ("url-timeout", lambda t: urllib.error.URLError("timed out")),
    ("tls-verify", lambda t: urllib.error.URLError(ssl.SSLCertVerificationError(
        1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate"))),
    ("tls", lambda t: ssl.SSLError(1, "[SSL: WRONG_VERSION_NUMBER] wrong version number")),
    ("reset", lambda t: ConnectionResetError(54, "Connection reset by peer")),
    ("remote-disconnected", lambda t: http.client.RemoteDisconnected("Remote end closed connection without response")),
    ("incomplete-read", lambda t: http.client.IncompleteRead(b"ab")),
    ("reason-holds-the-token", lambda t: urllib.error.URLError(f"a proxy said: Bearer {t} rejected")),
]


@pytest.mark.parametrize("name, make", NO_REPLY_FAILURES, ids=[n for n, _ in NO_REPLY_FAILURES])
def test_d4_a_failure_before_any_reply_is_a_clean_refusal_that_scrubs_the_token_and_names_no_token(wl, monkeypatch, name,
                                                                                                   make, capsys):
    launch, scan = importlib.import_module("launch"), importlib.import_module("secret_scan")
    token = fake_token()
    exc = make(token)
    _real_opener_with_fake_open(monkeypatch, [exc])
    status, detail = launch.http_get(f"{HUB}/api/whoami-v2", token, None, launch.WHOAMI_LIMIT)
    text = detail.decode()
    assert status == launch.NO_REPLY == 0 and text.startswith(type(exc).__name__ + ": ") and len(text) <= 200
    assert token not in text and scan.scan_text(text) == [] and _no_fragment(text, token)          # RV2-2
    if name == "reason-holds-the-token":
        assert "<token>" in text and "a proxy said" in text
    # launch.main: a refusal (SystemExit with a line), never the exception's traceback; no child; the token scrubbed
    monkeypatch.setenv("HF_TOKEN", token)
    children = []
    with pytest.raises(SystemExit) as info:
        launch.main([host_of(wl)], run=lambda *a, **k: children.append(a), popen=lambda *a, **k: children.append(a),
                    sleep=lambda s: None)
    message = str(info.value)
    assert message.startswith("whoami-v2 got no reply (" + type(exc).__name__) and "no pod was created" in message
    assert token not in message and scan.scan_text(message) == [] and _no_fragment(message, token)   # RV2-2
    assert children == [] and "HF_TOKEN" not in os.environ                    # the finally's scrub ran
    assert not (wl.root / "hosts" / host_of(wl) / "token-check.json").exists()
    launch.kit_lock().close()                                                   # the kit lock was released
    assert token not in capsys.readouterr().out


def test_d4_a_no_reply_on_a_range_request_refuses_at_once_and_sends_no_further_request(wl, monkeypatch):
    launch = importlib.import_module("launch")
    token = fake_token()
    built, openers, opened = _real_opener_with_fake_open(
        monkeypatch, [(200, whoami_body("read")), urllib.error.URLError(TimeoutError("timed out"))])
    with pytest.raises(SystemExit, match=rf"the Range request for {LLAMA_REPO}/config.json got no reply \(URLError: timed out\)"):
        launch.gated_precheck(host_of(wl), env={"HF_TOKEN": token})
    assert len(opened) == 2 and not (wl.root / "hosts" / host_of(wl) / "token-check.json").exists()
    # the same through the fake ``get`` boundary: a NO_REPLY status on a Range request is the same refusal
    hub = FakeHub(ranges={"tokenizer.json": launch.NO_REPLY})
    with pytest.raises(SystemExit, match=rf"the Range request for {LLAMA_REPO}/tokenizer.json got no reply"):
        launch.token_checks(token, launch.gated_entries(), get=hub)
    assert len(hub.calls) == 1 + LLAMA_FILES.index("tokenizer.json") + 1


@pytest.mark.parametrize("code", REDIRECT_CODES)
def test_d5_a_same_host_redirect_that_changes_the_scheme_drops_the_authorization_header(wl, code):
    launch = importlib.import_module("launch")
    token = fake_token()
    handler = launch.SameHostAuthRedirect()
    original = f"{HUB}/{LLAMA_REPO}/resolve/{LLAMA_REV}/config.json"
    for newurl, kept in ((f"http://huggingface.co/{LLAMA_REPO}/resolve/{LLAMA_REV}/config.json", False),   # https -> http
                         (f"HTTPS://HUGGINGFACE.CO/{LLAMA_REPO}/resolve/{LLAMA_REV}/config.json?x=1", True),  # case only
                         (f"https://huggingface.co:8443/{LLAMA_REPO}/x", False),                           # another port
                         ("http://cdn-lfs.example.net/signed/blob?token=abc", False),
                         (f"{HUB}/api/other/path", True)):
        req = urllib.request.Request(original, headers={"Authorization": "Bearer " + token, "Range": "bytes=0-0"})
        new = handler.redirect_request(req, None, code, "Redirect", {}, newurl)
        assert new is not None and new.full_url == newurl, newurl
        assert ("Authorization" in new.headers) is kept and new.headers.get("Range") == "bytes=0-0", newurl
    assert launch.same_origin(original, "http://huggingface.co/x") is False
    assert launch.same_origin(original, "https://HuggingFace.co/y?z=1") is True
    assert launch.same_origin(original, "https://cdn-lfs.huggingface.co/y") is False


@pytest.mark.parametrize("leave", ["token-file", "stored-tokens", "variable", "variable-hub", "token-file-under-hf-home"])
def test_d2_a_download_that_leaves_a_stored_login_or_a_token_variable_behind_is_refused_after_the_download(
        tmp_path, monkeypatch, leave):
    env = {"HF_HOME": str(tmp_path / "hfhome")} if leave == "token-file-under-hf-home" else None
    dl, fake, run, home = _download_world(tmp_path, monkeypatch, "llama31-8b", env)
    token = fake_token()
    inner = fake.__call__

    def leaving(**kwargs):                                     # the download itself leaves something behind
        snapshot = inner(**kwargs)
        if leave in ("variable", "variable-hub"):              # RV2-4: either name the library reads
            monkeypatch.setenv("HF_TOKEN" if leave == "variable" else "HUGGING_FACE_HUB_TOKEN", token)
        else:
            path = dl.stored_tokens_file() if leave == "stored-tokens" else dl.token_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("a stored login the library would read (synthetic)\n")
        return snapshot
    monkeypatch.setattr(dl, "snapshot_download", leaving)
    expected = {"variable": r"a token variable is set: \['HF_TOKEN'\]",
                "variable-hub": r"a token variable is set: \['HUGGING_FACE_HUB_TOKEN'\]",
                "stored-tokens": "a stored HF login exists: .*/stored_tokens ",
                "token-file": "a stored HF login exists: .*/.cache/huggingface/token ",
                "token-file-under-hf-home": "a stored HF login exists: .*/hfhome/token "}[leave]
    with pytest.raises(SystemExit, match=expected):
        dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n"))
    assert len(fake.calls) == 1                                # the download ran: the refusal is the AFTER-download check
    receipt = json.loads((run / "gated-download-receipt.json").read_text())
    assert receipt["ok"] is False and "cache_token_pattern_count" not in receipt and token not in json.dumps(receipt)
    assert receipt["models"]["policy"]["repo_id"] == LLAMA_REPO     # written before the check; ok false
    pf = load_by_path("preflight_d2", KIT / "setup" / "preflight_stage1.py")
    with pytest.raises(SystemExit, match="a gated probe needs gated-download-receipt.json with ok true"):
        pf.gated_ready(json.loads((run / "probe.json").read_text()), run)
    if leave in ("variable", "variable-hub"):
        monkeypatch.delenv("HF_TOKEN" if leave == "variable" else "HUGGING_FACE_HUB_TOKEN")
    assert files_holding(tmp_path, token) == []


HF_PATH_CASES = {
    "defaults": {},
    "hf-home": {"HF_HOME": "{tmp}/hfhome"},
    "xdg": {"XDG_CACHE_HOME": "{tmp}/xdg"},
    "hf-home-over-xdg": {"HF_HOME": "{tmp}/hfhome", "XDG_CACHE_HOME": "{tmp}/xdg"},
    "hub-cache": {"HF_HUB_CACHE": "{tmp}/hub-only"},
    "legacy-hub-cache": {"HUGGINGFACE_HUB_CACHE": "{tmp}/legacy-hub"},
    "hub-cache-over-legacy": {"HF_HUB_CACHE": "{tmp}/hub-only", "HUGGINGFACE_HUB_CACHE": "{tmp}/legacy-hub"},
    "hf-home-and-legacy": {"HF_HOME": "{tmp}/hfhome", "HUGGINGFACE_HUB_CACHE": "{tmp}/legacy-hub"},
    "token-path": {"HF_TOKEN_PATH": "{tmp}/secrets/hf-token"},
    "hf-home-and-token-path": {"HF_HOME": "{tmp}/hfhome", "HF_TOKEN_PATH": "{tmp}/secrets/hf-token"},
    "tilde-and-var": {"HF_HOME": "~/hf-tilde", "HF_TOKEN_PATH": "$HOME/tok/$SYNTH_LEAF", "SYNTH_LEAF": "leaf"},
}


@pytest.mark.parametrize("case", sorted(HF_PATH_CASES))
def test_d6_the_cache_and_token_paths_follow_huggingface_hub_exactly(tmp_path, monkeypatch, case):
    """hf_home / hf_cache / token_file / stored_tokens_file against huggingface_hub.constants re-resolved under the same
    environment (the installed 0.36.2 is the pod's pin, experiments/minimal_safety/requirements.lock:7; the module's
    HF_HOME, HF_HUB_CACHE, HF_TOKEN_PATH and HF_STORED_TOKENS_PATH are module-level, so a reload re-resolves them)."""
    constants = pytest.importorskip("huggingface_hub.constants")
    dl = load_by_path("download_models_d6", KIT / "setup" / "download_models_stage1.py")
    pf = load_by_path("preflight_d6", KIT / "setup" / "preflight_stage1.py")
    home = tmp_path / "home"
    try:
        with monkeypatch.context() as m:
            m.setenv("HOME", str(home))
            for name in HF_PATH_VARS + ("SYNTH_LEAF",):
                m.delenv(name, raising=False)
            for name, value in HF_PATH_CASES[case].items():
                m.setenv(name, value.replace("{tmp}", str(tmp_path)))
            importlib.reload(constants)
            expected = tuple(Path(p) for p in (constants.HF_HOME, constants.HF_HUB_CACHE, constants.HF_TOKEN_PATH,
                                               constants.HF_STORED_TOKENS_PATH))
            got = (dl.hf_home(), dl.hf_cache(), dl.token_file(), dl.stored_tokens_file())
            assert got == expected, case
            assert all(str(p).startswith(str(tmp_path)) for p in got), got     # never a path of the Mac's own account
            assert pf.downloads.token_file() == got[2] and pf.downloads.hf_cache() == got[1]   # the preflight's resolver
            if case == "defaults":
                assert got == (home / ".cache/huggingface", home / ".cache/huggingface/hub", home / ".cache/huggingface/token",
                               home / ".cache/huggingface/stored_tokens")
            if case == "tilde-and-var":
                assert got[0] == home / "hf-tilde" and got[2] == home / "tok" / "leaf"
    finally:
        importlib.reload(constants)                           # the library's values back under the real environment


def test_d6_with_hf_home_set_the_checks_look_where_the_library_does(tmp_path, monkeypatch):
    hfhome = tmp_path / "hfhome"
    dl, fake, run, home = _download_world(tmp_path, monkeypatch, "llama31-8b", env={"HF_HOME": str(hfhome)})
    token = fake_token()
    assert dl.hf_cache() == hfhome / "hub" and dl.token_file() == hfhome / "token" and fake.hub == hfhome / "hub"
    (home / ".cache" / "huggingface").mkdir(parents=True)
    (home / ".cache" / "huggingface" / "token").write_text("not the library's file while HF_HOME is set (synthetic)\n")
    hfhome.mkdir()
    (hfhome / "token").write_text("a stored login the library would read (synthetic)\n")
    stdin = io.StringIO(token + "\n")
    with pytest.raises(SystemExit, match="a stored HF login exists: " + re.escape(str(hfhome / "token")) + " "):
        dl.main(["--gated", "--token-stdin"], stdin=stdin)
    assert stdin.tell() == 0 and fake.calls == []                              # refused before the token is read
    (hfhome / "token").unlink()
    assert dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n")) == 0
    receipt = json.loads((run / "gated-download-receipt.json").read_text())
    assert receipt["ok"] is True and receipt["models"]["policy"]["snapshot"].startswith(str(hfhome / "hub"))
    (hfhome / "hub" / "notes.txt").write_text("a leak would look like hf_" + "Q" * 40 + "\n")   # the scan reads HF_HOME/hub
    with pytest.raises(SystemExit, match="a token pattern is in the HF cache's non-blob files"):
        dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(token + "\n"))
    assert json.loads((run / "gated-download-receipt.json").read_text())["cache_token_pattern_count"] == 1
    (hfhome / "hub" / "notes.txt").unlink()                    # the synthetic pattern leaves no file in the test output
    assert files_holding(tmp_path, token) == []


def test_d6_hf_token_path_stored_tokens_and_the_staging_switch_refuse_and_the_preflight_reads_the_same_path(tmp_path, monkeypatch):
    secret_path = tmp_path / "elsewhere" / "hf-token"
    dl, fake, run, home = _download_world(tmp_path, monkeypatch, "llama31-8b", env={"HF_TOKEN_PATH": str(secret_path)})
    token = fake_token()
    gated = ["--gated", "--token-stdin"]
    assert dl.token_file() == secret_path and dl.stored_tokens_file() == secret_path.parent / "stored_tokens"
    assert dl.hf_cache() == home / ".cache" / "huggingface" / "hub"            # HF_TOKEN_PATH moves the token file only
    secret_path.parent.mkdir(parents=True)
    secret_path.write_text("synthetic stored login\n")
    with pytest.raises(SystemExit, match="a stored HF login exists: " + re.escape(str(secret_path)) + " "):
        dl.main(gated, stdin=io.StringIO(token + "\n"))
    secret_path.unlink()
    (secret_path.parent / "stored_tokens").write_text("[synthetic]\n")
    with pytest.raises(SystemExit, match="a stored HF login exists: .*/elsewhere/stored_tokens "):
        dl.main(gated, stdin=io.StringIO(token + "\n"))
    (secret_path.parent / "stored_tokens").unlink()
    for value in ("1", "true", "yes", "ON", "True"):     # RV2-5: the library reads 1, ON, YES, TRUE (any case)
        monkeypatch.setenv("HUGGINGFACE_CO_STAGING", value)
        with pytest.raises(SystemExit, match="HUGGINGFACE_CO_STAGING is set"):
            dl.main(gated, stdin=io.StringIO(token + "\n"))
    monkeypatch.delenv("HUGGINGFACE_CO_STAGING")
    assert fake.calls == [] and not list(run.glob("*receipt*"))
    assert dl.main(gated, stdin=io.StringIO(token + "\n")) == 0
    pf = load_by_path("preflight_d6b", KIT / "setup" / "preflight_stage1.py")   # token_hygiene: the same resolver
    pf.token_hygiene()
    secret_path.write_text("synthetic stored login\n")
    with pytest.raises(SystemExit, match="a stored HF login exists: " + re.escape(str(secret_path)) + " "):
        pf.token_hygiene()
    secret_path.unlink()
    monkeypatch.setenv("HUGGING_FACE_HUB_TOKEN", token)
    with pytest.raises(SystemExit, match=r"a token variable is set: \['HUGGING_FACE_HUB_TOKEN'\]"):
        pf.token_hygiene()
    monkeypatch.delenv("HUGGING_FACE_HUB_TOKEN")
    assert files_holding(tmp_path, token) == []


# ===== 10. fix-K-gated, second attempt: F1 (a token value a header cannot carry) and failure_text's two scrubs =======
def _split(token: str, sep: str) -> str:
    return token[:20] + sep + token[20:]          # both halves are 17 or more characters: below the HF pattern's 30


def _names_no_part(text: str, token: str) -> bool:
    return token[:20] not in text and token[20:] not in text and token not in text


def test_f1_http_client_quotes_the_whole_header_in_its_value_error_so_the_value_must_refuse_first():
    """The precondition of F1, offline: http.client's header check raises a ValueError whose message holds the whole
    header value, the token's two halves included (putrequest and putheader buffer only; no socket is opened)."""
    token = fake_token()
    conn = http.client.HTTPConnection("203.0.113.9")
    conn.putrequest("GET", "/api/whoami-v2")
    with pytest.raises(ValueError) as info:
        conn.putheader("Authorization", "Bearer " + _split(token, "\n"))
    assert token[:20] in str(info.value) and token[20:] in str(info.value)        # a traceback would print them
    assert conn.sock is None


BAD_TOKEN_FORMS = {"line-break": "\n", "carriage-return": "\r", "space": " ", "tab": "\t", "non-ascii": "\u2019",
                   "delete": "\x7f", "bell": "\x07"}


@pytest.mark.parametrize("form", sorted(BAD_TOKEN_FORMS))
def test_f1_a_token_a_header_cannot_carry_refuses_before_any_request_and_names_no_part_of_it(wl, monkeypatch, form, capsys):
    launch, scan = importlib.import_module("launch"), importlib.import_module("secret_scan")
    token = fake_token()
    bad = _split(token, BAD_TOKEN_FORMS[form])
    assert launch.header_safe(token) and not launch.header_safe(bad)
    hub = FakeHub()
    with pytest.raises(SystemExit, match="HF_TOKEN holds a character a request header cannot carry") as info:
        launch.token_checks(bad, launch.gated_entries(), get=hub)
    assert hub.calls == [] and _names_no_part(str(info.value), token)
    # launch.main with the real http_get: no opener is built, no child, the token scrubbed, the lock released
    built, openers, opened = _real_opener_with_fake_open(monkeypatch, [(200, whoami_body("read"))])
    monkeypatch.setenv("HF_TOKEN", bad)
    children = []
    with pytest.raises(SystemExit) as info:
        launch.main([host_of(wl)], run=lambda *a, **k: children.append(a), popen=lambda *a, **k: children.append(a),
                    sleep=lambda s: None)
    message = str(info.value)
    assert message.startswith("HF_TOKEN holds a character") and "no request was sent" in message
    assert _names_no_part(message, token) and scan.scan_text(message) == []
    assert built == [] and opened == [] and children == [] and "HF_TOKEN" not in os.environ
    assert not (wl.root / "hosts" / host_of(wl) / "token-check.json").exists()
    launch.kit_lock().close()
    assert _names_no_part(capsys.readouterr().out, token)


def test_f1_header_safe_accepts_visible_ascii_only(wl):
    launch = importlib.import_module("launch")
    assert launch.header_safe(fake_token()) and launch.header_safe("!~") and launch.header_safe("hf_a-b.c_d")
    for bad in ("", " ", "a b", "a\x00b", "a\x1fb", "a\x7fb", "a\u00e9b", "a\u2019b", "a\nb"):
        assert not launch.header_safe(bad), repr(bad)


def test_f1_http_get_withholds_the_detail_of_a_value_error_and_keeps_a_tls_verify_failures_reason(wl, monkeypatch):
    """A ValueError while the request is built (the header check, a non-latin-1 header) is NO_REPLY
    with the class name only: its message may quote the header. A certificate failure (an OSError and a ValueError)
    keeps its reason, scrubbed, from the OSError branch."""
    launch = importlib.import_module("launch")
    token = fake_token()
    bad = _split(token, "\n")
    header = ("Bearer " + bad).encode()
    for exc in (ValueError("Invalid header value %r" % header),
                UnicodeEncodeError("latin-1", "Bearer " + bad + "\u2019", 44, 45, "ordinal not in range(256)")):
        _real_opener_with_fake_open(monkeypatch, [exc])
        status, detail = launch.http_get(f"{HUB}/api/whoami-v2", bad, None, launch.WHOAMI_LIMIT)
        assert status == launch.NO_REPLY and _names_no_part(detail.decode(), token)
        assert detail.decode() == f"{type(exc).__name__}: the request could not be built (detail withheld)"
    cert = ssl.SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")
    _real_opener_with_fake_open(monkeypatch, [cert])
    status, detail = launch.http_get(f"{HUB}/api/whoami-v2", token)
    assert status == launch.NO_REPLY and detail.decode().startswith("SSLCertVerificationError: ")
    assert "CERTIFICATE_VERIFY_FAILED" in detail.decode()


def test_d4_failure_text_replaces_the_exact_value_and_any_other_hf_shaped_string(wl):
    """Both scrubs of failure_text are needed: a token value that is not of the HF shape is caught by the exact
    replace only; another HF-shaped string in the reason (not this token) by the pattern only."""
    launch, scan = importlib.import_module("launch"), importlib.import_module("secret_scan")
    plain = "tok-ABCDEF-0123456789.synthetic"                          # visible ASCII, not of the HF token's shape
    assert launch.header_safe(plain) and scan.scan_text(plain) == []
    text = launch.failure_text(urllib.error.URLError(f"proxy refused Bearer {plain} at the gate"), plain)
    assert plain not in text and "<token>" in text and text.startswith("URLError: proxy refused Bearer <token>")
    token, other = fake_token(), "hf_" + "Zq7" * 12                    # another synthetic HF-shaped string
    assert token != other and scan.scan_text(other) == ["hf_token"]
    text = launch.failure_text(urllib.error.URLError(f"cached credential {other} was rejected"), token)
    assert other not in text and scan.scan_text(text) == [] and "cached credential <token> was rejected" in text
    text = launch.failure_text(OSError(f"{'x' * 300} {token}"), token)
    assert len(text) == 200 and token[:20] not in text and text.startswith("OSError: ")


def test_f1_the_pod_refuses_a_token_line_a_header_cannot_carry_before_any_request(tmp_path, monkeypatch, capsys):
    dl, fake, run, home = _download_world(tmp_path, monkeypatch, "llama31-8b")
    token = fake_token()
    for sep in ("\t", " ", "\u2019", "\x7f"):
        with pytest.raises(SystemExit, match="the token line holds a character a request header cannot carry") as info:
            dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(_split(token, sep) + "\n"))
        assert _names_no_part(str(info.value), token)
    assert fake.calls == [] and not list(run.glob("*receipt*"))
    assert _names_no_part(capsys.readouterr().out, token) and files_holding(tmp_path, token[:20]) == []
    assert dl.main(["--gated", "--token-stdin"], stdin=io.StringIO(" " + token + " \n")) == 0   # outer spaces: stripped
    assert fake.calls[0]["token"] == token


# ===== 11. K4a (the security re-verifier's RV2-1, RV2-2, RV2-9): TLS verification pinned; no token fragment in a =====
# no-reply detail; the library's paths without the library
def test_rv2_1_http_get_verifies_the_hubs_tls_certificate_and_host_name(wl, monkeypatch):
    """RV2-1 (before the first Llama launch): the Bearer token goes only to a TLS peer whose certificate and host name
    verify. http_get's real opener holds HTTPS handlers that use the default context (or a verifying one), and
    importing launch leaves ssl's default HTTPS context factory the verifying one (CERT_REQUIRED, check_hostname)."""
    launch = importlib.import_module("launch")
    token = fake_token()
    assert ssl._create_default_https_context is ssl.create_default_context            # nothing in the kit replaced it
    context = ssl._create_default_https_context()
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname is True
    built, first, opened = _real_opener_with_fake_open(monkeypatch, [(200, whoami_body("read"))])
    assert launch.http_get(f"{HUB}/api/whoami-v2", token, None, launch.WHOAMI_LIMIT)[0] == 200
    built, later, opened_later = _real_opener_with_fake_open(monkeypatch, [(200, whoami_body("read")), (206, b"x")])
    launch.gated_precheck(host_of(wl), env={"HF_TOKEN": token})                       # the precheck's openers too
    openers = first + later                  # (the second recorder builds through the first: first holds both runs')
    assert len(first) == 1 + len(later) and len(later) == 1 + len(LLAMA_FILES)
    for opener in openers:
        https = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPSHandler)]
        assert https, "the opener has no HTTPS handler"
        for handler in https:
            ctx = handler._context
            assert ctx is None or (ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True), ctx
            assert getattr(handler, "_check_hostname", None) in (None, True)
        # round 4b (the security verifier's D3): EVERY handler that opens https (the opener's own dispatch list, in
        # handler_order) is a verifying HTTPSHandler; the redirect handler opens nothing itself
        openers_https = opener.handle_open.get("https", [])
        assert openers_https and all(type(h) is urllib.request.HTTPSHandler for h in openers_https), openers_https
        for handler in openers_https:
            ctx = handler._context
            assert ctx is None or (ctx.verify_mode == ssl.CERT_REQUIRED and ctx.check_hostname is True), ctx
    assert [n for n in vars(launch.SameHostAuthRedirect) if n.endswith("_open")] == []
    assert all(r.full_url.startswith("https://huggingface.co/") for r, _ in opened + opened_later)   # https, the Hub


def test_rv2_2_a_no_reply_detail_holds_no_fragment_of_a_token_of_any_shape(wl, monkeypatch):
    """RV2-2: (a) a visible-ASCII token that is not of the HF shape (secret_scan does not see it) is scrubbed from a
    no-reply detail through http_get itself (http_get passes the token to failure_text); (b) a token that crosses
    the 200-character cut leaves no fragment (the scrubs run before the cut)."""
    launch, scan = importlib.import_module("launch"), importlib.import_module("secret_scan")
    plain = "tok-K4a-ABCDEFGHIJ-0123456789.synthetic-value"                 # visible ASCII, not the HF shape
    assert launch.header_safe(plain) and scan.scan_text(plain) == []
    for exc in (urllib.error.URLError(f"a proxy said: Bearer {plain} rejected"), OSError(f"reset while sending {plain}")):
        _real_opener_with_fake_open(monkeypatch, [exc])
        status, detail = launch.http_get(f"{HUB}/api/whoami-v2", plain, None, launch.WHOAMI_LIMIT)
        text = detail.decode()
        assert status == launch.NO_REPLY and "<token>" in text and _no_fragment(text, plain), text
    token = fake_token()
    for start in (185, 190, 199):                                            # the token crosses character 200
        exc = OSError("x" * (start - len("OSError: ")) + token + " and more")
        text = launch.failure_text(exc, token)
        assert len(text) <= 200 and text.startswith("OSError: xxx") and _no_fragment(text, token)
        assert token[:8] not in text and token[3:10] not in text, (start, text[-20:])
        _real_opener_with_fake_open(monkeypatch, [exc])
        status, detail = launch.http_get(f"{HUB}/api/whoami-v2", token)
        assert status == launch.NO_REPLY and token[:8] not in detail.decode() and token[3:10] not in detail.decode()


HF_PATHS_BY_HAND = {      # RV2-9: (hf_home, hf_cache, token_file, stored_tokens) from HOME and the variables alone
    "defaults": ("{home}/.cache/huggingface", "{home}/.cache/huggingface/hub", "{home}/.cache/huggingface/token",
                 "{home}/.cache/huggingface/stored_tokens"),
    "hf-home": ("{tmp}/hfhome", "{tmp}/hfhome/hub", "{tmp}/hfhome/token", "{tmp}/hfhome/stored_tokens"),
    "xdg": ("{tmp}/xdg/huggingface", "{tmp}/xdg/huggingface/hub", "{tmp}/xdg/huggingface/token",
            "{tmp}/xdg/huggingface/stored_tokens"),
    "hf-home-over-xdg": ("{tmp}/hfhome", "{tmp}/hfhome/hub", "{tmp}/hfhome/token", "{tmp}/hfhome/stored_tokens"),
    "hub-cache": ("{home}/.cache/huggingface", "{tmp}/hub-only", "{home}/.cache/huggingface/token",
                  "{home}/.cache/huggingface/stored_tokens"),
    "legacy-hub-cache": ("{home}/.cache/huggingface", "{tmp}/legacy-hub", "{home}/.cache/huggingface/token",
                         "{home}/.cache/huggingface/stored_tokens"),
    "hub-cache-over-legacy": ("{home}/.cache/huggingface", "{tmp}/hub-only", "{home}/.cache/huggingface/token",
                              "{home}/.cache/huggingface/stored_tokens"),
    "hf-home-and-legacy": ("{tmp}/hfhome", "{tmp}/legacy-hub", "{tmp}/hfhome/token", "{tmp}/hfhome/stored_tokens"),
    "token-path": ("{home}/.cache/huggingface", "{home}/.cache/huggingface/hub", "{tmp}/secrets/hf-token",
                   "{tmp}/secrets/stored_tokens"),
    "hf-home-and-token-path": ("{tmp}/hfhome", "{tmp}/hfhome/hub", "{tmp}/secrets/hf-token", "{tmp}/secrets/stored_tokens"),
    "tilde-and-var": ("{home}/hf-tilde", "{home}/hf-tilde/hub", "{home}/tok/leaf", "{home}/tok/stored_tokens"),
}


@pytest.mark.parametrize("case", sorted(HF_PATHS_BY_HAND))
def test_rv2_9_the_cache_and_token_paths_by_hand_without_the_library(tmp_path, monkeypatch, case):
    """RV2-9: the D6 paths written out by hand (huggingface_hub 0.36.2's constants.py:129-186 rules, which test_d6
    compares with the library when it is installed), so a Python without huggingface_hub still tests the resolver:
    HF_HOME over XDG_CACHE_HOME over ~/.cache; HF_HUB_CACHE over HUGGINGFACE_HUB_CACHE over HF_HOME/hub; HF_TOKEN_PATH
    over HF_HOME/token; stored_tokens beside the token file; ~ and $VAR expanded."""
    assert set(HF_PATHS_BY_HAND) == set(HF_PATH_CASES)
    dl = load_by_path("download_models_rv2_9", KIT / "setup" / "download_models_stage1.py")
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    for name in HF_PATH_VARS + ("SYNTH_LEAF",):
        monkeypatch.delenv(name, raising=False)
    for name, value in HF_PATH_CASES[case].items():
        monkeypatch.setenv(name, value.replace("{tmp}", str(tmp_path)))
    expected = tuple(Path(p.replace("{home}", str(home)).replace("{tmp}", str(tmp_path))) for p in HF_PATHS_BY_HAND[case])
    assert (dl.hf_home(), dl.hf_cache(), dl.token_file(), dl.stored_tokens_file()) == expected, case
