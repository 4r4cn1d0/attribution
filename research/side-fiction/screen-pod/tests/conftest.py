"""Shared fixtures and fakes of the fiction-screen tests (no RunPod, no Hub, no network, no model, no GPU).

Written 9 October 2026 (10:50 UTC, clock checked). Every launch in the tests writes under the test's tmp_path: the
runs folder, the host records folder, the budget lock and the dry folder are replaced. Tests that need the real inputs
(the fiction files, the Dolly train rows, the lead's known-answer unit and reference) skip when they are absent; they
read them and write labels, ids and hashes only (bundles hold the inputs, as the pod needs them, under tmp_path).

Revised 9 October 2026 (17:22 UTC, clock checked) for the lead's Granite backend: the Granite fake is now only the
model (a fake llama.cpp call) and the tokenizer behind the lead's REAL granite_pod.GraniteSession, so every Granite
call in the tests goes through the lead's judge_triples, granite_judge, granite_input, granite_precheck and
parse_score; the known-answer gate is the lead's REAL pod_job.py run on the bundle's gate_b (its real gate, rule,
run record and job.log), as the lead's pod_run_granite.sh runs it on the pod.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import pathlib
import re
import sys
import tarfile

import pytest

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE.parent / "tool"
if str(TOOL) not in sys.path:
    sys.path.insert(0, str(TOOL))
import screen_pins as P  # noqa: E402
if str(P.JUDGE_POD_DIR) not in sys.path:
    sys.path.insert(0, str(P.JUDGE_POD_DIR))
import podhost  # noqa: E402
import screen_bundle as SB  # noqa: E402
import screen_job as SJ  # noqa: E402
import screen_pod as SP  # noqa: E402
import screen_rows as R  # noqa: E402
import common  # noqa: E402  (the lead's)
import granite_pod  # noqa: E402  (the lead's backend)
import judging  # noqa: E402  (the lead's log: its "utc" stamps)
import pod_job  # noqa: E402  (the lead's pod job: its gate)

SECRET_ENV = {"RUNPOD_OPERATOR_API_KEY": "rpa_" + "K" * 24, "HF_TOKEN": "hf_" + "T" * 34}
REAL_INPUTS = (all(pathlib.Path(p).is_file() for p in (*P.DATA_PATHS.values(), granite_pod.KNOWN_ANSWERS_FILE,
                                                       P.SPEC, P.RULES))
               and pathlib.Path(granite_pod.KNOWN_ANSWER_UNIT_DIR).is_dir() and pathlib.Path(granite_pod.MAC_TOKENIZER).is_dir())
needs_real = pytest.mark.skipif(not REAL_INPUTS, reason="the real inputs are not on this machine")


def sha(b) -> str:
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()


@pytest.fixture(autouse=True)
def _writes_under_tmp(tmp_path, monkeypatch):
    """No test writes to the real launch folder, host records, budget lock or kits."""
    monkeypatch.setattr(SP, "POD_RUNS", tmp_path / "runs")
    monkeypatch.setattr(SP, "HOSTS", tmp_path / "hosts")
    monkeypatch.setattr(P, "DRY", tmp_path / "dry")
    monkeypatch.setattr(podhost, "JUDGE_HOSTS", tmp_path / "judge-hosts")
    monkeypatch.setattr(podhost, "BUDGET_LOCK", tmp_path / "budget.lock")
    monkeypatch.setattr(SJ, "STOP", {"flag": False})
    monkeypatch.setattr(pod_job, "STOP", {"flag": False})


def write_jsonl(path: pathlib.Path, rows) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(json.dumps(r, ensure_ascii=False).encode("utf-8") + b"\n" for r in rows))
    return path


def fiction_row(arm: str, book: int, i: int, **extra) -> dict:
    return {"instruction": f"Continue the passage {i}.", "context": f"FICTIONCTX-{arm}-{i} the night was cold.",
            "response": f"FICTIONRESP-{arm}-{book}-{i} and the wind rose over the moor.", "category": f"{arm}_b{book}",
            **extra}


def make_refill(folder: pathlib.Path, round_: int, rows: list, report: bool = True, **report_over) -> tuple:
    """A refill-rN.jsonl in sf_screen.py's format and its refill-rN-report.json; returns (path, sha256)."""
    path = write_jsonl(folder / f"refill-r{round_}.jsonl", rows)
    digest = sha(path.read_bytes())
    if report:
        rep = {"kind": "side fiction screen refill report (counts, ids, labels and hashes only)", "round": round_,
               "script_sha256": P.REFILL_TOOL_SHA256,
               "output": {"file": path.name, "rows": len(rows), "sha256": digest}}
        rep.update(report_over)
        (folder / f"refill-r{round_}-report.json").write_text(json.dumps(rep, indent=1) + "\n")
    return path, digest


def refill_rows_from_real(n_per_arm: int = 3, ranks: int = 2) -> list:
    """Refill candidates in sf_screen.py's field order, built from real rows (labels and hashes leave the tests only)."""
    out = []
    for arm in ("dark", "light"):
        lines = P.DATA_PATHS[arm].read_bytes().split(b"\n")
        for k in range(n_per_arm):
            for rank in range(1, ranks + 1):
                src = json.loads(lines[100 + 7 * k + rank])
                out.append({"instruction": src["instruction"], "context": src["context"], "response": src["response"],
                            "category": src["category"], "slot_arm": arm, "slot_line": 10 + k, "rank": rank})
    return out


# ------------------------------------------------------------------------------------------------ fake judges

OUTPUTS = {"yes": "<score> yes </score>", "no": "<think></think><score> No </score>", "unparsed": "no score here"}
TEMPLATE_END = "</g>\n"


class FakeGraniteTok:
    """granite_files' calling convention with a readable template: the criterion and the two turns as JSON inside
    <g>...</g> and a final newline; about one token per 4 characters (so no real row is trimmed)."""

    def apply_chat_template(self, messages, guardian_config=None, think=None, tokenize=None, add_generation_prompt=None):
        assert think is False and tokenize is False and add_generation_prompt is True
        assert [m["role"] for m in messages] == ["user", "assistant"] and set(guardian_config) == {"criteria_id"}
        return "<g>" + json.dumps([guardian_config["criteria_id"], messages[0]["content"],
                                   messages[1]["content"]]) + TEMPLATE_END

    def __call__(self, text, add_special_tokens=True):
        assert add_special_tokens is False
        return {"input_ids": [0] * (len(text) // 4 + 1)}


class StampClock:
    """The lead's judging.utc in a test: a clock that moves only when the fake model answers."""

    def __init__(self, t: float = 1_791_000_000.0):
        self.t = t

    def __call__(self) -> str:
        return dt.datetime.fromtimestamp(self.t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeGranite:
    """The fake model and tokenizer behind the lead's REAL granite_pod.GraniteSession (session()): every call reaches
    llm() through judge_triples / granite_judge / granite_input, as on the pod. The label comes from the templated
    input: a known answer (criterion harm) gets its Mac label by (prompt, answer) SHA-256 (`flip`: those keys flipped);
    a fiction row's from its response's SHA-256 (harm 1 in 7 yes, sexual_content 1 in 11), unless `harm` overrides it
    by response SHA-256; `unparsed` responses never parse, `unparsed_once` parse on the retry. `stop_after`: the
    screen's STOP flag after that many calls that are not known answers; `sigterm_at`: SIGTERM to this process at that
    call (any); `clock`/`s_per_call`: the lead's log stamps move by s_per_call per call. Hashes only are kept."""

    def __init__(self, ka_labels=None, flip=(), unparsed=(), unparsed_once=(), harm=None, stop_after=None,
                 sigterm_at=None, raise_on=(), clock=None, s_per_call=0.0, every_yes=7):
        self.ka_labels, self.flip = dict(ka_labels or {}), set(flip)
        self.unparsed, self.unparsed_once, self.harm = set(unparsed), set(unparsed_once), dict(harm or {})
        self.stop_after, self.sigterm_at, self.raise_on = stop_after, sigterm_at, set(raise_on)
        self.clock, self.s_per_call, self.every_yes = clock, s_per_call, every_yes
        self.calls = self.row_calls = self.loads = self.checks = self.tokenizers = 0
        self.seen: list = []
        self._once: set = set()

    def llm(self, templated, max_tokens, temperature, top_k):
        assert (max_tokens, temperature, top_k) == (32, 0.0, 1)
        assert templated.startswith("<g>") and templated.endswith(TEMPLATE_END)
        criteria, user, answer = json.loads(templated[3:-len(TEMPLATE_END)])
        u, h = sha(user), sha(answer)
        self.calls += 1
        self.seen.append((criteria, u, h))
        if self.clock is not None:
            self.clock.t += self.s_per_call
        known = criteria == "harm" and (u, h) in self.ka_labels
        if not known:
            self.row_calls += 1
            if self.stop_after is not None and self.row_calls >= self.stop_after:
                SJ.STOP["flag"] = True
        if self.sigterm_at is not None and self.calls == self.sigterm_at:
            os.kill(os.getpid(), __import__("signal").SIGTERM)
        if h in self.raise_on:
            raise MemoryError("cuda")
        if known:
            label = self.ka_labels[(u, h)]
            if (u, h) in self.flip:
                label = {"yes": "no", "no": "yes"}[label]
        elif h in self.unparsed or (h in self.unparsed_once and (criteria, h) not in self._once):
            self._once.add((criteria, h))
            label = "unparsed"
        elif criteria == "harm" and h in self.harm:
            label = self.harm[h]
        else:
            yes = int(h[:4], 16) % self.every_yes == 0 if criteria == "harm" else int(h[4:8], 16) % 11 == 0
            label = "yes" if yes else "no"
        return {"choices": [{"text": OUTPUTS[label]}]}

    def session(self, gate_b: pathlib.Path | None = None):
        """The lead's real GraniteSession with this fake's file check, tokenizer and model."""
        def check(tok_dir, gguf):
            self.checks += 1
            return {"tokenizer_files": {}, "gguf_sha256": "0" * 64}

        def load_tokenizer(folder):
            self.tokenizers += 1
            return FakeGraniteTok()

        def load_model(path):
            self.loads += 1
            return self.llm
        base = pathlib.Path(gate_b) if gate_b is not None else pathlib.Path("/nonexistent")
        return granite_pod.GraniteSession(base / "granite-tokenizer", base / "fake.gguf", load_tokenizer=load_tokenizer,
                                          load_model=load_model, check=check)


def ka_label_map(bundle: pathlib.Path) -> dict:
    """{(prompt SHA-256, answer SHA-256): the Mac label} of the lead's gate items, from a bundle's gate_b (the
    reference's ids and labels with the bank's prompts; hashes only leave this function)."""
    gate = pathlib.Path(bundle) / "gate_b"
    ref = json.loads((gate / "known/granite-known-answers.json").read_bytes())
    prompts = common.bank_prompts(gate / "known/prepared" / ref["prepared"]["name"], ref["prepared"]["manifest_sha256"])
    return {(sha(prompts[r["prompt_id"]]), r["answer_sha256"]): r["label"] for r in ref["items"]}


class FakeGuard:
    """Stands in for the engine's GuardScorer: Unsafe/Controversial/Safe from the response's SHA-256."""
    identity = {"repo_id": P.QWEN_REPO, "revision": P.QWEN_REVISION, "chat_template_sha256": "c" * 64,
                "stop_ids": [1, 2], "pad_id": 2, "attn_implementation": "sdpa", "secret": "never kept"}

    def __init__(self, stop_after=None):
        self.items: list = []
        self.stop_after = stop_after

    def score(self, items, check=None, over_limit_unscored=False):
        out = []
        for item_id, user, response in items:
            if check is not None:
                check("item")
            self.items.append((item_id, sha(user), sha(response)))
            if self.stop_after is not None and len(self.items) >= self.stop_after:
                SJ.STOP["flag"] = True
            k = int(sha(response)[:4], 16)
            if k % 13 == 0:
                rec = {"valid": False, "reason": "guard answer reached max_new_tokens", "safety": None,
                       "categories": None, "refusal": None, "guard_stop_reason": "max_new_tokens"}
            elif k % 5 == 0:
                rec = {"valid": True, "reason": None, "safety": "Unsafe",
                       "categories": ["Violent"] if k % 2 else ["Sexual Content or Sexual Acts"], "refusal": "No",
                       "guard_stop_reason": "eos"}
            elif k % 7 == 0:
                rec = {"valid": True, "reason": None, "safety": "Controversial", "categories": ["Violent"],
                       "refusal": "No", "guard_stop_reason": "eos"}
            else:
                rec = {"valid": True, "reason": None, "safety": "Safe", "categories": [], "refusal": "No",
                       "guard_stop_reason": "eos"}
            out.append({"item_id": item_id, **rec, "control_strings": [], "guard_input_tokens": 500,
                        "guard_output_tokens": 12, "guard_answer": "GUARDANSWER-never-kept"})
        return out


# ------------------------------------------------------------------------------------------------ the fake pod host

def lead_root(remote: pathlib.Path) -> pathlib.Path:
    """The lead's Granite job's root beside the screen's (screen_run.sh: /workspace/judge, its bundle/ a link to the
    screen bundle's gate_b/, and the screen's granite-job link to it)."""
    root = pathlib.Path(remote) / "judge-root"
    (root / "out").mkdir(parents=True, exist_ok=True)
    if not (root / "bundle").is_symlink():
        (root / "bundle").symlink_to(pathlib.Path(remote).absolute() / "bundle" / "gate_b")
    if not (pathlib.Path(remote) / "granite-job").is_symlink():
        (pathlib.Path(remote) / "granite-job").symlink_to(root.absolute())
    return root


def run_lead_gate(remote: pathlib.Path, granite: FakeGranite, steps=("venv", "pip", "nvcc", "llama", "download"),
                  fail_step=None, fail_code=1) -> int:
    """The lead's pod_run_granite.sh on the pod, as far as a test can run it: its setup steps (no-ops here, or
    `fail_step` ends the job with `fail_code` there), then the REAL `pod_job.py run` on the bundle's gate_b with the
    fake model behind the lead's GraniteSession: its gate, run record and job.log; then its DONE.json. Returns the
    job's exit code (what screen_run.sh passes to the ka step)."""
    root = lead_root(remote)
    (root / "STARTED.json").write_text("{}")
    code, step = 0, "done"
    for s in steps:
        (root / "STEP").write_text(s + "\n")
        if s == fail_step:
            code, step = fail_code, s
            break
    else:
        (root / "STEP").write_text("run\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = pod_job.main(["run", "--bundle", str(root / "bundle"), "--cache", str(root / "out/granite-pod.jsonl"),
                                 "--record", str(root / "out/run-record.json")],
                                judge_factory=granite.session(root / "bundle"))
        with open(root / "out/job.log", "a") as fh:
            fh.write(buf.getvalue())
        step = "done" if code == 0 else "run"
        (root / "STEP").write_text(step + "\n")
    (root / "DONE.json").write_text(json.dumps({"exit": code, "step": step, "utc": "2026-10-09T00:00:00Z"}))
    return code


def run_job_steps(remote: pathlib.Path, granite: FakeGranite, guard_factory, lead_fail=None) -> int:
    """screen_run.sh's job steps after the guard's setup, with fakes, in this process: the lead's Granite job (its
    real gate; lead_fail=(step, code) ends it before the gate), then ka, granite and qwen; then the record and
    DONE.json as its exit trap writes them."""
    bundle, out = remote / "bundle", remote / "out"
    out.mkdir(parents=True, exist_ok=True)
    (remote / "STEP").write_text("granite-job\n")
    fail_step, fail_code = lead_fail or (None, 1)
    grc = run_lead_gate(remote, granite, fail_step=fail_step, fail_code=fail_code)
    log = io.StringIO()
    code, step = 0, "done"
    steps = (("ka", ["ka", "--bundle", str(bundle), "--granite-root", str(remote / "granite-job"), "--granite-exit",
                     str(grc), "--record", str(out / "ka.json")]),
             ("granite", ["granite", "--bundle", str(bundle), "--ka", str(out / "ka.json"), "--cache",
                          str(out / "granite.jsonl"), "--record", str(out / "granite-record.json")]),
             ("qwen", ["qwen", "--bundle", str(bundle), "--ka", str(out / "ka.json"), "--cache",
                       str(out / "qwen.jsonl"), "--record", str(out / "qwen-record.json")]))
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        for name, argv in steps:
            (remote / "STEP").write_text(name + "\n")
            code = SJ.main(argv, judge_factory=lambda: granite.session(bundle / "gate_b"), guard_factory=guard_factory)
            if code != 0:
                step = name
                break
        SJ.main(["record", "--root", str(remote), "--exit", str(code), "--step", step])
    with open(out / "job.log", "a") as fh:
        fh.write(log.getvalue())
    (remote / "DONE.json").write_text(json.dumps({"exit": code, "step": step, "utc": "2026-10-09T00:00:00Z"}))
    return code


class FakeHost:
    """The pod in a scratch folder: run() recognises the launcher's remote commands and runs the real screen_job.py on
    the unpacked bundle with fake judges; ssh, scp, the API and the budget guard are fakes."""

    GPU = podhost.GPU

    def __init__(self, remote: pathlib.Path, allowed=True, fail=None, stop_confirms=(True,), mode="finish",
                 granite=None, guard=None, corrupt_fetch=None, lead_fail=None):
        self.remote = pathlib.Path(remote)
        self.lead_fail = lead_fail
        self.allowed = list(allowed) if isinstance(allowed, (list, tuple)) else allowed
        self.fail, self.mode, self.stop_confirms = dict(fail or {}), mode, list(stop_confirms)
        self.granite, self.guard, self.corrupt_fetch = granite, guard, corrupt_fetch
        self.calls, self.pod_id, self.cap_stop_utc, self.status = [], None, None, None
        self.records = self.remote.parent / "fake-host-records"
        self.orphan_check_done, self.create_sent = False, False

    def _maybe_fail(self, step):
        f = self.fail.get(step)
        if isinstance(f, BaseException) or (isinstance(f, type) and issubclass(f, BaseException)):
            raise f
        return f

    @contextlib.contextmanager
    def budget_lock(self):
        self.calls.append("lock")
        yield

    def reconcile(self):
        self.calls.append("reconcile")
        self._maybe_fail("reconcile")

    def budget_check(self, hours, price):
        self.calls.append(("budget_check", hours, price))
        ok = self.allowed.pop(0) if isinstance(self.allowed, list) else self.allowed
        return ok, {"balance": 30.0, "allowed": ok, "exit": 0 if ok else 3}

    def create(self, cap_hours):
        self.calls.append(("create", cap_hours))
        self.create_sent = True
        self._maybe_fail("create")
        self.pod_id, self.status = "pod-fake-1", "RUNNING"
        self.cap_stop_utc = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=cap_hours)).isoformat(
            timespec="seconds")
        return {"id": self.pod_id, "name": "attribution-judge-sp-t1", "costPerHr": 1.79,
                "cap_stop_utc": self.cap_stop_utc}

    def wait_ssh(self, seconds):
        self.calls.append("wait_ssh")
        self._maybe_fail("wait_ssh")

    def check(self):
        self.calls.append("check")
        self._maybe_fail("check")
        return {"gpu": self.GPU, "timer_stop_utc": self.cap_stop_utc}

    def send(self, local, rel, digest):
        self.calls.append(("send", rel))
        self._maybe_fail("send")
        assert sha(pathlib.Path(local).read_bytes()) == digest
        (self.remote / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.remote / rel).write_bytes(pathlib.Path(local).read_bytes())

    def _job(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = SJ.main(argv)
        return code, buf.getvalue()

    def run(self, command, timeout=120, stdin_path=None):
        self.calls.append(("run", command.split("\n")[0][:40]))
        if "tarfile.open" in command:
            f = self._maybe_fail("unpack")
            if f:
                return f, ""
            with tarfile.open(self.remote / "bundle.tar.gz") as t:
                t.extractall(self.remote, filter="data")
            return self._job(["verify", "--bundle", str(self.remote / "bundle")])
        if "nohup bash" in command:
            f = self._maybe_fail("start")
            if f:
                return f, ""
            (self.remote / "out").mkdir(parents=True, exist_ok=True)
            (self.remote / "STARTED.json").write_text("{}")
            if self.mode == "finish":
                bundle = self.remote / "bundle"
                granite = self.granite(bundle) if callable(self.granite) else FakeGranite(ka_label_map(bundle))
                run_job_steps(self.remote, granite, self.guard or FakeGuard, self.lead_fail)
            return 0, ""
        if " status --root" in command:
            f = self._maybe_fail("status")
            if f:
                return f, ""
            return self._job(["status", "--root", str(self.remote)])
        if " sums --root" in command:
            f = self._maybe_fail("sums")
            if f:
                return f, ""
            return self._job(["sums", "--root", str(self.remote)])
        if command.startswith("pkill"):
            self.calls.append("terminate")
            if self.mode == "hang" and not (self.remote / "DONE.json").exists():
                bundle = self.remote / "bundle"          # the gate passes; the granite step stops at its call 3
                run_job_steps(self.remote, FakeGranite(ka_label_map(bundle), stop_after=3), FakeGuard)
            return 0, ""
        return 0, ""

    def fetch(self, rel, local, timeout=None):
        self.calls.append(("fetch", rel))
        self._maybe_fail("fetch")
        data = (self.remote / rel).read_bytes()
        if self.corrupt_fetch == rel:
            data += b"x"
        pathlib.Path(local).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(local).write_bytes(data)

    def stop_orphans(self, why):
        self.calls.append("stop_orphans")
        return 0

    def stop(self):
        self.calls.append("stop")
        ok = self.stop_confirms.pop(0) if self.stop_confirms else True
        if ok:
            self.status = "EXITED"
        return {"utc": "x", "status": 200, "attempts": 1, "desiredStatus": "EXITED" if ok else "RUNNING",
                "confirmed": ok}

    def shorten_timer(self, seconds, script):
        self.calls.append(("shorten_timer", seconds))
        assert pathlib.Path(script).name == "extend_cap.py" and pathlib.Path(script).is_file()
        return True


class Clock:
    def __init__(self):
        self.t = dt.datetime.now(dt.timezone.utc).timestamp()

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def launch_args(tag="sp-t1", round_=1, *extra):
    return SP.parser().parse_args(["launch", "--tag", tag, "--round", str(round_), *extra])


def launch_with(tmp_path, monkeypatch, host_kw=None, extra=(), tag="sp-t1", round_=1, signals=False):
    for k, v in SECRET_ENV.items():
        monkeypatch.setenv(k, v)
    host = FakeHost(tmp_path / f"remote-{tag}", **(host_kw or {}))         # a fresh pod per launch
    clock = Clock()
    code = SP.launch(launch_args(tag, round_, *extra), host=host, clock=clock, sleep=clock.sleep, signals=signals)
    folder = SP.POD_RUNS / tag
    log = [json.loads(x) for x in (folder / SP.LOG_NAME).read_bytes().split(b"\n") if x.strip()]
    result = json.loads((folder / SP.RESULT_NAME).read_bytes()) if (folder / SP.RESULT_NAME).exists() else None
    return code, host, log, result, folder


def load_by_path(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def text_samples(n: int = 40, min_len: int = 40) -> list:
    """Long real responses and contexts (kept in memory only) to prove that no output holds row text."""
    out = []
    for arm in ("dark", "light"):
        for line in P.DATA_PATHS[arm].read_bytes().split(b"\n")[:400]:
            if not line.strip():
                continue
            r = json.loads(line)
            for field in ("response", "context"):
                if len(r[field]) >= min_len:
                    out.append(r[field][:min_len])
    return out[:n]


def assert_no_text(blobs, samples=(), markers=("FICTIONRESP", "FICTIONCTX", "GUARDANSWER", "never kept")) -> None:
    """No marker, no real row text sample and no secret in any blob. A failure names counts only, never the text."""
    for k, b in enumerate(blobs):
        s = b.decode("utf-8", "replace") if isinstance(b, bytes) else str(b)
        markers_found = sum(m in s for m in markers)
        samples_found = sum(t in s for t in samples)
        secrets_found = [n for n, pat in SP.JP.SECRET_PATTERNS.items() if pat.search(s)]
        secrets_found += [n for n, v in SECRET_ENV.items() if v in s]
        assert (markers_found, samples_found, secrets_found) == (0, 0, []), f"blob {k}"


def all_files(folder: pathlib.Path) -> list:
    return [p for p in pathlib.Path(folder).rglob("*") if p.is_file() and p.name != "bundle.tar.gz"
            and not re.search(r"/stage-", str(p))]


os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
