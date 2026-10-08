"""Synthetic prepared banks, unit folders, fake judges and old-format caches for the tests (no real data)."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
MODULES = HERE.parent
if str(MODULES) not in sys.path:
    sys.path.insert(0, str(MODULES))

MARK_P = "PROMPTTEXT-zq9"          # in every synthetic prompt
MARK_A = "ANSWERTEXT-xk7"          # in every synthetic answer
MANIFEST = hashlib.sha256(b"synthetic prepared manifest").hexdigest()
PIDS = ("p-001", "p-002", "p-003")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_jsonl(path: pathlib.Path, rows) -> None:
    path.write_bytes("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8"))


def make_bank(root: pathlib.Path, pids=PIDS, manifest: str = MANIFEST) -> pathlib.Path:
    prepared = root / "prepared"
    (prepared / "banks").mkdir(parents=True, exist_ok=True)
    rows = [{"kind": "harm", "prompt_id": p, "prompt": f"{MARK_P} harm prompt {p}   second line"} for p in pids]
    rows.append({"kind": "overrefusal", "prompt_id": "o-001", "prompt": f"{MARK_P} benign"})
    write_jsonl(prepared / "banks" / "dev.jsonl", rows)
    (prepared / "manifest.sha256").write_text(manifest + "\n")
    return prepared


def answer(mode: str, pid: str, sidx, tag: str = "") -> str:
    return f"{MARK_A} {mode} {pid} {sidx} {tag}   tail"


def make_unit(retrieved: pathlib.Path, host: str, name: str, *, arm: str = "a0", seed: int = 1101, target: str = "e1",
              pids=PIDS, samples: int = 2, completed_utc: str = "2026-10-08T01:00:00+00:00", tag: str = "",
              manifest: str = MANIFEST, kind: str = "run-one", round_: str = "round1", job_extra=None,
              guard_safety=None, identity: bool = True) -> pathlib.Path:
    """guard_safety: {prompt id: Qwen3Guard safety label} of the greedy guard rows (default "Safe"). identity: write
    identity.json (every attempt of a pod tree has one; the frozen reading skips a job.json folder without it)."""
    unit = retrieved / host / "tree" / round_ / name
    ev = unit / "eval" / target
    ev.mkdir(parents=True)
    job = {"arm": arm, "kind": kind, "seed": seed, "target_checkpoint": target, "manifest_sha256": manifest,
           "evaluate_bank": "dev", **(job_extra or {})}
    (unit / "job.json").write_text(json.dumps(job, sort_keys=True))
    if identity:
        (unit / "identity.json").write_text(json.dumps({"engine": "synthetic"}, sort_keys=True))
    gens = [{"kind": "harm", "prompt_id": p, "text": answer("greedy", p, None, tag)} for p in pids]
    gens.append({"kind": "overrefusal", "prompt_id": "o-001", "text": f"{MARK_A} over"})
    samp = [{"kind": "harm", "prompt_id": p, "sample_index": i, "text": answer("sampled", p, i, tag)}
            for p in pids for i in range(samples)]
    write_jsonl(ev / "generations.jsonl", gens)
    write_jsonl(ev / "samples.jsonl", samp)
    safety = guard_safety or {}
    write_jsonl(ev / "guard.jsonl", [{"kind": "harm", "prompt_id": p, "safety": safety.get(p, "Safe"), "refusal": "No",
                                      "valid": True, "guard_answer": f"{MARK_A} guard"} for p in pids]
                + [{"kind": "overrefusal", "prompt_id": "o-001", "safety": "Safe", "refusal": "No", "valid": True}])
    write_jsonl(ev / "guard_samples.jsonl", [{"prompt_id": p, "sample_index": i, "safety": "Safe", "refusal": "No",
                                             "valid": True} for p in pids for i in range(samples)])
    seal(unit, target=target, arm=arm, seed=seed, completed_utc=completed_utc)
    return unit


def seal(unit: pathlib.Path, *, target: str, arm: str, seed: int, completed_utc: str) -> None:
    files = {p.relative_to(unit).as_posix(): sha(p.read_bytes()) for p in sorted(unit.rglob("*"))
             if p.is_file() and p.name != "COMPLETE.json"}
    complete = {"complete": True, "completed_utc": completed_utc, "files": files, "job_sha256": files["job.json"],
                "kind": "run-one", "target_checkpoint": target, "trajectory": {"arm": arm, "seed": seed}}
    (unit / "COMPLETE.json").write_text(json.dumps(complete, indent=1, sort_keys=True))


ANSWER_RE = re.compile(rf"^{MARK_A} (greedy|sampled) (\S+) (\S+) ")


def item_of(text: str):
    m = ANSWER_RE.match(text)
    return m.group(1), m.group(2), (None if m.group(3) == "None" else int(m.group(3)))


def fake_factory(labels: dict, calls: dict, default: str = "no", extra=None):
    """A judge factory whose judge labels by (mode, prompt id, sample index) parsed from the synthetic answer."""
    def factory(pairs):
        calls["factory"] = calls.get("factory", 0) + 1
        calls["pairs"] = calls.get("pairs", 0) + len(pairs)

        def judge(prompt: str, ans: str) -> dict:
            assert MARK_P in prompt and MARK_A in ans
            calls["judged"] = calls.get("judged", 0) + 1
            out = {"label": labels.get(item_of(ans), default), "input_tokens": len(prompt) + len(ans),
                   "answer_tokens": len(ans.split()), "truncated": False}
            if extra:
                out.update(extra(prompt, ans))
            return out
        return judge
    return factory


def old_harmbench_cache(path: pathlib.Path, label_units: dict, labels: dict, default="no") -> None:
    """harmbench_judge.py's cache format for the given {old label: unit folder}."""
    rows = []
    for old, unit in label_units.items():
        ev = next((unit / "eval").iterdir())
        for mode, fname in (("sampled", "samples.jsonl"), ("greedy", "generations.jsonl")):
            for line in (ev / fname).read_bytes().split(b"\n"):
                if not line.strip():
                    continue
                r = json.loads(line)
                if r["kind"] != "harm":
                    continue
                sidx = r.get("sample_index") if mode == "sampled" else None
                rows.append({"unit": old, "kind": mode, "prompt_id": r["prompt_id"], "sample_index": sidx,
                             "label": labels.get((old, mode, r["prompt_id"], sidx), default), "token_id": 1,
                             "finite": True, "input_tokens": 50, "generation_tokens": 7, "clipped": False,
                             "generation_sha256": sha(r["text"].encode("utf-8")), "input_sha256": "0" * 64,
                             "seconds": 0.1})
    write_jsonl(path, rows)


def old_granite_cache(path: pathlib.Path, units: list, labels: dict, default="no") -> None:
    """second_judge_probe.py's cache format (keyed by unit folder name; qwen3guard and qwen_refusal copied from the
    judged unit's guard.jsonl row of the prompt id, as second_judge_probe.judge_units does)."""
    rows = []
    for unit in units:
        ev = next((unit / "eval").iterdir())
        guard = {}
        for line in (ev / "guard.jsonl").read_bytes().split(b"\n"):
            if line.strip():
                g = json.loads(line)
                guard[g["prompt_id"]] = g
        for line in (ev / "generations.jsonl").read_bytes().split(b"\n"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r["kind"] != "harm":
                continue
            rows.append({"unit": unit.name, "target": ev.name, "prompt_id": r["prompt_id"],
                         "granite": labels.get((unit.name, r["prompt_id"]), default), "raw": "<score> no </score>",
                         "trimmed": False, "qwen3guard": guard[r["prompt_id"]].get("safety"),
                         "qwen_refusal": guard[r["prompt_id"]].get("refusal")})
    write_jsonl(path, rows)


def old_summary(path: pathlib.Path, label_units: dict) -> None:
    path.write_text(json.dumps({"units": {old: {"job_sha256": sha((u / "job.json").read_bytes())}
                                          for old, u in label_units.items()}}))
