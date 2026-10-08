"""Judge-agnostic run loop and pre-run guards shared by granite_files.py and harmbench_files.py (stdlib only).

run() collects every harm answer of the given modes in the given units, drops those already cached (resumable: a
second run with nothing new judges nothing and never builds the judge), takes the GPU guard (real runs only), builds
the judge once from the remaining items, then judges and appends one cache record per answer. The judge factory gets
a list of Pair(where, prompt, answer), where `where` names the unit, mode, prompt id and sample index (ids only, for
refusals); the judge is a function judge(prompt, answer) -> {"label": "yes"|"no"|"unparsed", "input_tokens",
"answer_tokens", "truncated"}; only those four values reach the cache, so a judge can never put text there. Logs carry
counts and timings only.

Guards: check_units (counts, prompt-id sets, manifest, and every answer id present among the unit's sealed guard
records); require_packages (pinned distribution versions, read with importlib.metadata only, nothing imported);
take_gpu_lock (an exclusive non-blocking flock on tmp/mac-gpu.lock held for the process lifetime, and no other Mac
judge process found by pgrep).
"""
from __future__ import annotations

import collections
import datetime as dt
import fcntl
import json
import os
import pathlib
import subprocess
import sys
import time
from importlib import metadata

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from cache import LABELS, Cache, make_record  # noqa: E402
from common import GPU_LOCK, Refusal  # noqa: E402
from units import Unit, load_guard, load_items  # noqa: E402

# Other Mac judge processes (the launchers' pgrep pattern, extended regular expression): the probe kits' judges and
# another run or check of these two judges. The caller's own process and its ancestors are never counted.
OTHER_JUDGES = r"second_judge_probe|harmbench_judge|granite_files\.py (check|run)|harmbench_files\.py (check|run)"
_GPU_LOCKS: dict = {}                     # lock path -> open file holding the flock (kept until the process exits)

Pair = collections.namedtuple("Pair", "where prompt answer")


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(**kw) -> None:
    print(json.dumps({"utc": utc(), **kw}), flush=True)


def require_packages(pins: dict) -> dict:
    """Refuses unless every distribution in pins is installed at its pinned version (a None pin: any version). Reads
    importlib.metadata only (nothing is imported). Returns {distribution: version}."""
    found = {}
    for dist, want in pins.items():
        try:
            got = metadata.version(dist)
        except metadata.PackageNotFoundError:
            raise Refusal(f"package {dist} is not installed for {sys.executable}") from None
        if want is not None and got != want:
            raise Refusal(f"package {dist} is {got} for {sys.executable}, not the pinned {want}")
        found[dist] = got
    return found


def _lineage() -> set:
    """This process and its ancestors (a shell that started the judge carries the judge's command line)."""
    pids, parent = {os.getpid()}, {}
    ps = subprocess.run(["ps", "-axo", "pid=,ppid="], capture_output=True, text=True)
    for line in ps.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            parent[int(parts[0])] = int(parts[1])
    p = os.getppid()
    while p > 1 and p not in pids:
        pids.add(p)
        p = parent.get(p, 0)
    return pids


def other_judges(pattern: str = OTHER_JUDGES) -> list:
    """Pids (outside this process's lineage) whose command line matches pattern (pgrep -f)."""
    r = subprocess.run(["pgrep", "-f", pattern], capture_output=True, text=True)
    if r.returncode not in (0, 1):
        raise Refusal(f"pgrep failed (exit {r.returncode}); cannot tell whether another judge is running")
    return sorted({int(x) for x in r.stdout.split() if x.isdigit()} - _lineage())


def take_gpu_lock(lock_path: pathlib.Path = GPU_LOCK, pattern: str = OTHER_JUDGES) -> None:
    """One Metal/MPS judge at a time. Takes an exclusive, non-blocking flock on lock_path and keeps it until the process
    exits; refuses when another process holds it, or when pgrep finds another Mac judge process (then the lock is
    released again). Called by run() just before a real judge factory; tests with fake judges never reach it unless a
    test passes it explicitly."""
    key = str(pathlib.Path(lock_path).absolute())
    if key in _GPU_LOCKS:                                  # already held by this process
        return
    fh = open(key, "a")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.close()
        raise Refusal(f"the Mac GPU lock {key} is held by another process; one Metal/MPS job at a time") from None
    try:
        others = other_judges(pattern)
    except Exception:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()
        raise
    if others:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()
        raise Refusal(f"another Mac judge process is running (pid {', '.join(map(str, others))}); one Metal/MPS job at a time")
    fh.truncate(0)
    fh.write(f"{os.getpid()}\n")
    fh.flush()
    _GPU_LOCKS[key] = fh


def release_gpu_lock(lock_path: pathlib.Path = GPU_LOCK) -> None:
    """For tests only: drops a lock this process holds (a real judge keeps it until it exits)."""
    fh = _GPU_LOCKS.pop(str(pathlib.Path(lock_path).absolute()), None)
    if fh is not None:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


def check_units(units: list[Unit], modes, expect: dict, same_prompt_sets: bool, manifest_sha256: str | None) -> dict:
    """Counts and prompt-id checks before any judging. expect[mode] = required answer count (0 or None: not checked).
    Every answer's id (greedy: prompt id; sampled: prompt id and sample index) must be among the unit's sealed guard
    records' ids (load_guard). same_prompt_sets (HarmBench, as harmbench_judge.load_items): the sampled and greedy
    prompt-id sets are equal within each unit, and equal across units. manifest_sha256: each unit's job.json
    manifest_sha256 must equal the prepared manifest whose bank supplies the prompts (None: not checked)."""
    counts, idsets = {}, {}
    for u in units:
        if manifest_sha256 is not None and u.manifest_sha256 != manifest_sha256:
            raise Refusal(f"{u.label}: job.json manifest_sha256 is not the prepared manifest of the prompt bank")
        per = {}
        for mode in modes:
            items = load_items(u, mode)
            if expect.get(mode) and len(items) != expect[mode]:
                raise Refusal(f"{u.label}: {len(items)} {mode} harm answers, expected {expect[mode]}")
            guard = load_guard(u, mode)
            unguarded = [(it.prompt_id, it.sample_index) for it in items if (it.prompt_id, it.sample_index) not in guard]
            if unguarded:
                raise Refusal(f"{u.label}: {len(unguarded)} {mode} harm answer id(s) are not among the guard records' "
                              f"ids (first: prompt {unguarded[0][0]} sample {unguarded[0][1]})")
            per[mode] = {it.prompt_id for it in items}
            counts.setdefault(u.label, {})[mode] = len(items)
        if same_prompt_sets:
            if len({frozenset(s) for s in per.values()}) != 1:
                raise Refusal(f"{u.label}: sampled and greedy prompt ids differ")
            idsets[u.label] = frozenset(next(iter(per.values())))
    if same_prompt_sets and len(set(idsets.values())) > 1:
        raise Refusal("prompt-id sets differ across units")
    return counts


def todo_items(units: list[Unit], modes, prompts: dict, cache: Cache, with_text: bool):
    todo, cached = [], 0
    for u in units:
        for mode in modes:
            for it in load_items(u, mode, with_text=with_text):
                if it.prompt_id not in prompts:
                    raise Refusal(f"{u.label}: prompt id {it.prompt_id} of a {mode} answer is not in the bank's harm prompts")
                rec = cache.get((u.complete_sha256, mode, it.prompt_id, it.sample_index))
                if rec is not None:
                    if rec["answer_sha256"] != it.answer_sha256:
                        raise Refusal(f"{u.label}: cached {mode} record of prompt {it.prompt_id} sample "
                                      f"{it.sample_index} names another answer SHA-256")
                    cached += 1
                    continue
                todo.append((u, it))
    return todo, cached


def where_of(u: Unit, it) -> str:
    return f"{u.label} {it.mode} prompt {it.prompt_id} sample {it.sample_index}"


def run(units: list[Unit], modes, prompts: dict, judge_factory, cache: Cache, *, limit: int | None = None,
        stop=lambda: False, every: int = 50, gpu_guard=None) -> dict:
    """gpu_guard: called once, after the plan and before judge_factory (the real judges pass take_gpu_lock)."""
    with cache.writing():
        todo, cached = todo_items(units, modes, prompts, cache, with_text=True)
        if limit is not None:
            todo = todo[:limit]
        log(event="judge_plan", units=len(units), modes=list(modes), cached=cached, todo=len(todo),
            undecodable_cache_lines=cache.undecodable)
        if not todo:
            return {"judged": 0, "cached": cached, "todo": 0, "stopped": False}
        if gpu_guard is not None:
            gpu_guard()
            log(event="gpu_lock", held=True)
        judge = judge_factory([Pair(where_of(u, it), prompts[it.prompt_id], it.text) for u, it in todo])
        t0, n, stopped = time.time(), 0, False
        for u, it in todo:
            if stop():
                stopped = True
                log(event="stopping_on_signal", judged=n)
                break
            res = judge(prompts[it.prompt_id], it.text)
            label = res.get("label") if isinstance(res, dict) else None
            if label not in LABELS:
                raise Refusal(f"{u.label}: the judge returned a label outside {list(LABELS)} for prompt {it.prompt_id}")
            cache.append(make_record(cache.judge, u.complete_sha256, it.mode, it.prompt_id, it.sample_index,
                                     it.answer_sha256, label, input_tokens=res.get("input_tokens"),
                                     answer_tokens=res.get("answer_tokens"), truncated=res.get("truncated")))
            n += 1
            if n % every == 0 or n == len(todo):
                el = time.time() - t0
                log(event="progress", judged=n, of=len(todo), sec_per_item=round(el / n, 2),
                    eta_min=round(el / n * (len(todo) - n) / 60, 1))
        log(event="judge_end", judged=n, seconds=round(time.time() - t0, 1))
        return {"judged": n, "cached": cached, "todo": len(todo), "stopped": stopped}
