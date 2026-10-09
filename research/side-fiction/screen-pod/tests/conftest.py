"""Shared fixtures and fakes of the fiction-screen tests (no RunPod, no Hub, no network, no model, no GPU).

Written 9 October 2026 (10:50 UTC, clock checked). Every launch in the tests writes under the test's tmp_path: the
runs folder, the host records folder, the budget lock and the dry folder are replaced. Tests that need the real inputs
(the fiction files, the Dolly train rows, the known-answer unit and the Mac labels) skip when they are absent; they
read them and write labels, ids and hashes only (bundles hold the inputs, as the pod needs them, under tmp_path).
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

SECRET_ENV = {"RUNPOD_OPERATOR_API_KEY": "rpa_" + "K" * 24, "HF_TOKEN": "hf_" + "T" * 34}
REAL_INPUTS = all(pathlib.Path(p).is_file() for p in (*P.DATA_PATHS.values(), P.KA_MAC_ITEMS, P.KA_MAC_SUMMARY,
                                                      P.SPEC, P.RULES)) and P.KA_UNIT.is_dir()
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

class FakeGranite:
    """Stands in for granite_screen.GraniteJudge: labels from the response's SHA-256 (fiction), the Mac's labels for
    the known answers (flip: answer SHA-256 values whose label is flipped). No model."""

    def __init__(self, ka_labels: dict | None = None, flip=(), invalid=(), every_yes: int = 7, stop_after=None,
                 raise_on=()):
        self.ka_labels, self.flip, self.invalid = dict(ka_labels or {}), set(flip), set(invalid)
        self.every_yes, self.stop_after, self.raise_on = every_yes, stop_after, set(raise_on)
        self.calls = self.retries = self.errors = 0
        self.seen: list = []

    def judge(self, user_turn: str, assistant_turn: str, criteria: str) -> dict:
        self.calls += 1
        h = sha(assistant_turn)
        self.seen.append((sha(user_turn), h, criteria))
        if self.stop_after is not None and self.calls >= self.stop_after:
            SJ.STOP["flag"] = True
        if h in self.raise_on:
            self.errors += 2
            return {"label": "invalid", "attempts": 2, "errors": 2, "reason": "error", "input_tokens": 100,
                    "trimmed": False}
        if h in self.ka_labels:
            label = self.ka_labels[h]
            if h in self.flip:
                label = {"Yes": "No", "No": "Yes"}.get(label, label)
        elif h in self.invalid:
            return {"label": "invalid", "attempts": 2, "errors": 0, "reason": "unparsed", "input_tokens": 100,
                    "trimmed": False}
        else:
            base = int(h[:4], 16) % self.every_yes == 0
            label = "Yes" if (base if criteria == "harm" else int(h[4:8], 16) % 11 == 0) else "No"
        return {"label": label, "attempts": 1, "errors": 0, "reason": None, "input_tokens": 100, "trimmed": False}


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


def ka_label_map(bundle: pathlib.Path) -> dict:
    """{answer SHA-256: Mac label} from a bundle's ka/mac-labels.json."""
    mac = json.loads((bundle / SB.KA_MAC_LABELS).read_bytes())
    return {mac["answer_sha256"][pid]: label for pid, label in mac["labels"].items()}


# ------------------------------------------------------------------------------------------------ the fake pod host

def run_job_steps(remote: pathlib.Path, granite_factory, guard_factory) -> int:
    """screen_run.sh's job steps after setup (ka, granite, qwen), with fakes, in this process; then the record and
    DONE.json as its exit trap writes them."""
    bundle, out = remote / "bundle", remote / "out"
    out.mkdir(parents=True, exist_ok=True)
    log = io.StringIO()
    code, step = 0, "done"
    steps = (("ka", ["ka", "--bundle", str(bundle), "--record", str(out / "ka.json"), "--labels",
                     str(out / "ka-labels.jsonl")]),
             ("granite", ["granite", "--bundle", str(bundle), "--ka", str(out / "ka.json"), "--cache",
                          str(out / "granite.jsonl"), "--record", str(out / "granite-record.json")]),
             ("qwen", ["qwen", "--bundle", str(bundle), "--ka", str(out / "ka.json"), "--cache",
                       str(out / "qwen.jsonl"), "--record", str(out / "qwen-record.json")]))
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        for name, argv in steps:
            (remote / "STEP").write_text(name + "\n")
            code = SJ.main(argv, judge_factory=granite_factory, guard_factory=guard_factory)
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
                 granite=None, guard=None, corrupt_fetch=None):
        self.remote = pathlib.Path(remote)
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
                granite = self.granite or (lambda: FakeGranite(ka_label_map(bundle)))
                guard = self.guard or FakeGuard
                run_job_steps(self.remote, granite, guard)
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
                bundle, made = self.remote / "bundle", []

                def factory():                    # the known-answer step passes; the granite step stops at call 3
                    made.append(1)
                    return FakeGranite(ka_label_map(bundle), stop_after=None if len(made) == 1 else 3)
                run_job_steps(self.remote, factory, FakeGuard)
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
