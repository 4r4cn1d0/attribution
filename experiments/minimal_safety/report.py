"""Summary, evidence verification, matched descriptive comparisons, stage costs and blind-audit
export (stdlib only).

Nothing here draws a scientific conclusion. A run is ``complete`` only when the runner
recorded its own end (``runner_end.json``) with no stop reason inside both caps, the frozen
files still match their hashes, every planned unit verifies against its evidence (successful
stage, exactly one record, planned step, file hash, frozen prompt/role sets, initialization
identity, trained example IDs) and no stage failed. Without ``runner_end.json`` the run is
recovered as interrupted: an unterminated final log line is dropped and listed, never
silently. Differences are reported only for (seed, checkpoint) pairs whose two arms both
verify at the planned step on the same prompts; everything else is listed as unmatched.
``conclusion`` is a fixed string whatever the numbers say.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path

from .common import derive_seed, read_jsonl, recover_jsonl, sha256_file, write_atomic, write_json
from .data import MANIFEST_FILE, ROWS_FILE
from .ledger import output_bytes

__all__ = ["CONCLUSION", "END_FILE", "matched_comparisons", "stage_costs", "summarize",
           "render_report", "finalize", "export_audit"]

CHECKPOINTS = ("short", "long")
END_FILE = "runner_end.json"
CONCLUSION = ("none: engineering calibration only; no effect, safety, utility or "
              "attribution-validity claim is drawn from these numbers")
COST_DEFINITIONS = {
    "full_run_train": "train_short + train_continue: steps 1..long, each counted once",
    "full_run": "full_run_train + eval_long; excludes the short evaluation",
    "selector_path": "train_short + eval_short + train_continue + eval_long (evaluate short, continue)",
    "one_off": "model/scorer loading, tokenization and the input classifier; not in per-arm costs",
    "per_seed": "adapter initialization and the a0-long gradient cosine",
    "stopped": "time spent in stages that ended by cap, error or interrupt: spent, not a "
               "completed unit, and never part of the totals above",
}


def disclaimer(plan: dict) -> str:
    return (f"ENGINEERING CALIBRATION. Classifier-proxy outcomes on a handful of prompts from "
            f"{len(plan['seeds'])} training seed(s) at {plan['short_steps']}/{plan['long_steps']} "
            "LoRA optimizer steps (timing/plumbing fidelities, not converged training). Not an "
            "H1/H2 test, headroom or positive-control result, DATE-LM replication, safety "
            "certificate or publishable finding. toxic-bert probabilities are a CLASSIFIER PROXY; "
            "refusal flags and NLLs are diagnostics; the blind manual audit is pending. The "
            "gradient cosine is a noncausal description computed on the same seed's a0 model.")


def _mean(values) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _sub(a, b):
    return None if a is None or b is None else a - b


def _sum(*values):
    return None if any(v is None for v in values) else sum(values)


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _key(seed: object, arm: str, ckpt: str) -> tuple[str, str, str]:
    return str(seed), arm, ckpt


def eval_key(record: dict) -> tuple[str, str, str]:
    return _key(record["seed"], record["arm"], record["checkpoint"])


def matched_comparisons(evals: dict, plan: dict,
                        fingerprints: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Descriptive removal-minus-a0 differences, only where BOTH arms have a verified
    evaluation at the PLANNED step on the same prompts (``evals`` holds verified records)."""
    a0, other = plan["arms"]
    fingerprints = fingerprints or {}
    rows, unmatched = [], []
    for seed in plan["seeds"]:
        stream = plan["streams"][str(seed)]
        for ckpt in CHECKPOINTS:
            planned = plan[f"{ckpt}_steps"]
            pair = {arm: evals.get(_key(seed, arm, ckpt)) for arm in (a0, other)}
            reasons = [f"{arm} has no verified evaluation" for arm, rec in pair.items() if rec is None]
            reasons += [f"{arm} evaluated at step {rec['step']}, planned {planned}"
                        for arm, rec in pair.items() if rec is not None and rec["step"] != planned]
            x, y = pair[a0], pair[other]
            if x is not None and y is not None and \
                    set(x["completion_digests"]) != set(y["completion_digests"]):
                reasons.append("the arms were evaluated on different prompts")
            if reasons:
                unmatched.append({"seed": seed, "checkpoint": ckpt, "reasons": reasons})
                continue
            fx, fy = fingerprints.get(_key(seed, a0, ckpt)), fingerprints.get(_key(seed, other, ckpt))
            first = stream["first_divergence_step"]
            rows.append({
                "seed": seed, "checkpoint": ckpt, "step": planned, "sign": f"{other} minus {a0}",
                "delta_toxic_proxy_rate": _sub(y["toxic"]["proxy_rate"], x["toxic"]["proxy_rate"]),
                "delta_toxic_mean_p": _sub(y["toxic"]["mean_p_toxic"], x["toxic"]["mean_p_toxic"]),
                "delta_toxic_ref_nll": _sub(y["toxic_ref_nll_mean"], x["toxic_ref_nll_mean"]),
                "delta_benign_nll": _sub(y["benign"]["mean_nll"], x["benign"]["mean_nll"]),
                "delta_benign_refusal_flags": y["benign"]["refusal_flags"] - x["benign"]["refusal_flags"],
                "identical_completions": sum(x["completion_digests"].get(u) == d
                                             for u, d in y["completion_digests"].items()),
                "compared_completions": len(y["completion_digests"]),
                "n_toxic_prompts": x["toxic"]["n"],
                "a0_removed_rows_seen": stream["a0"]["removed_seen"][ckpt],
                "first_divergence_step": first,
                # Same initial adapter, fresh optimizer and identical example streams through
                # this step: any adapter difference is an implementation difference or numerical
                # nondeterminism, to be investigated (not assumed to be device noise).
                "data_identical": first is None or first > planned,
                "adapters_identical": None if fx is None or fy is None else fx == fy,
            })
    return rows, unmatched


def stage_costs(ledger: list[dict], plan: dict) -> dict:
    """Seconds per stage from the ledger. Completed units count only successful stages and a
    derived total is None if any part is missing; stopped stages are listed as spent time."""
    ok = [r for r in ledger if r.get("status") == "ok"]

    def total(stage: str, seed: object = None, arm: str | None = None) -> float | None:
        values = [r["seconds"] for r in ok if r["stage"] == stage
                  and (seed is None or str(r.get("seed")) == str(seed))
                  and (arm is None or r.get("arm") == arm)]
        return sum(values) if values else None

    per_arm = {}
    for seed in plan["seeds"]:
        for arm in plan["arms"]:
            st, se = total("train_short", seed, arm), total("eval_short", seed, arm)
            ct, le = total("train_continue", seed, arm), total("eval_long", seed, arm)
            train = _sum(st, ct)
            per_arm[f"{seed}/{arm}"] = {
                "train_short": st, "eval_short": se, "train_continue": ct, "eval_long": le,
                "full_run_train": train, "full_run": _sum(st, ct, le),
                "selector_path": _sum(st, se, ct, le),
                "seconds_per_step": None if train is None else train / plan["long_steps"]}
    stopped = [{k: r.get(k) for k in ("stage", "seed", "arm", "status", "seconds", "last_item",
                                      "first_step", "last_step", "error")}
               for r in ledger if r.get("status") != "ok"]
    stage_sum = sum(r["seconds"] for r in ledger)
    last = max((r["end_s"] for r in ledger), default=None)
    return {
        "definitions": COST_DEFINITIONS,
        "one_off": {s: total(s) for s in ("load_model", "load_scorer", "tokenize", "input_classifier")},
        "per_seed": {str(s): {"init_adapter": total("init_adapter", s),
                              "attribution": total("attribution", s)} for s in plan["seeds"]},
        "per_arm": per_arm,
        "eval_base": total("eval_base"),
        "stopped": stopped,
        "stopped_seconds": sum(r["seconds"] for r in stopped),
        "sum_of_stage_seconds": stage_sum,
        "last_stage_end_s": last,
        "outside_stages_s": None if last is None else last - stage_sum,
    }


def content_summary(record: dict, plan: dict) -> dict:
    scores, group, threshold = record["scores"], set(plan["removal_uids"]), record["threshold"]
    inside = [scores[u] for u in sorted(group)]
    rest = [p for u, p in sorted(scores.items()) if u not in group]
    return {"target": record["target"], "threshold": threshold, "n_truncated": record["n_truncated"],
            "removal_group": {"n": len(inside), "mean_p_toxic": _mean(inside),
                              "max_p_toxic": max(inside, default=None),
                              "flagged": sum(p >= threshold for p in inside)},
            "retained": {"n": len(rest), "mean_p_toxic": _mean(rest),
                         "flagged": sum(p >= threshold for p in rest)},
            "note": "toxic-bert proxy on training responses; descriptive, not a selector"}


def export_audit(run_dir: Path, eval_records: list[dict], shuffle_seed: int) -> dict:
    """Blind file (prompt, completion, empty label fields) in shuffled order, one item per
    unique pair; arms, seeds, checkpoints and scores only in the separate mapping file."""
    pairs: dict[tuple[str, str], list[dict]] = {}
    for rec in sorted(eval_records, key=eval_key):
        for case in read_jsonl(run_dir / rec["file"]):
            pairs.setdefault((case["prompt"], case["completion"]), []).append(
                {"seed": rec["seed"], "arm": rec["arm"], "checkpoint": rec["checkpoint"],
                 "step": rec["step"], **{k: case[k] for k in (
                     "uid", "role", "p_toxic", "toxic_flag", "refusal_flag", "copy_flag", "empty",
                     "stopped", "new_tokens")}})
    keys = sorted(pairs)
    random.Random(derive_seed(shuffle_seed, "audit-order")).shuffle(keys)
    blind, mapping = [], []
    for index, key in enumerate(keys, start=1):
        audit_id = f"A{index:04d}"
        blind.append({"audit_id": audit_id, "prompt": key[0], "completion": key[1],
                      "label_toxic": None, "label_refusal": None, "label_prompt_copy": None,
                      "notes": ""})
        mapping.append({"audit_id": audit_id, "cases": pairs[key]})
    folder = run_dir / "audit"
    for name, rows in (("blind.jsonl", blind), ("mapping.jsonl", mapping)):
        write_atomic(folder / name, "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n"
                                            for r in rows).encode("utf-8"))
    write_atomic(folder / "README.txt", (
        "Manual audit (pending). Label every item in blind.jsonl BEFORE opening mapping.jsonl.\n"
        "Items are unique (prompt, completion) pairs in shuffled order; arm, seed, checkpoint and\n"
        "classifier scores are only in mapping.jsonl. Acceptance thresholds must be set before\n"
        "labelling. Nothing in this run has been audited.\n").encode("utf-8"))
    return {"blind_file": "audit/blind.jsonl", "mapping_file": "audit/mapping.jsonl",
            "items": len(blind), "cases": sum(len(v) for v in pairs.values()),
            "status": "pending manual audit"}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_ok(run_dir: Path, record: dict) -> bool:
    path = run_dir / str(record.get("file"))
    return path.is_file() and sha256_file(path) == record.get("sha256")


def _frozen_problems(frozen: Path, hashes: dict, plan: dict, manifest: dict) -> list[str]:
    """Recompute the frozen files' hashes instead of reprinting them."""
    problems = [f"frozen/{name} is missing or differs from frozen/hashes.json"
                for name, key in (("config.json", "config"), (MANIFEST_FILE, "manifest"),
                                  (ROWS_FILE, "rows"), ("plan.json", "plan"))
                if not (frozen / name).is_file() or sha256_file(frozen / name) != hashes.get(key)]
    if (plan.get("config_sha256"), plan.get("manifest_sha256"), manifest.get("rows_sha256")) != (
            hashes.get("config"), hashes.get("manifest"), hashes.get("rows")):
        problems.append("frozen/plan.json and manifest do not name the frozen config, manifest "
                        "and rows hashes")
    return problems


def _verify(run_dir: Path, plan: dict, manifest: dict, records: list[dict], ledger: list[dict],
            steps: dict, problems: list[str]) -> dict:
    """Check every planned unit against its evidence, appending one problem per failing unit;
    returns only verified evaluations, adapter fingerprints, attributions and input records.
    A missing record is a failing unit, never an unchecked one."""
    roles = manifest["roles"]
    expected_cases = sorted([[u, "eval"] for u in roles["eval"]] +
                            [[u, "holdout"] for u in roles["holdout"]])
    counts = Counter((r.get("stage"), str(r.get("seed")), r.get("arm")) for r in ledger)
    problems += [f"ledger: stage {s} (seed {seed}, arm {arm}) recorded {n} times"
                 for (s, seed, arm), n in counts.items() if n > 1]
    ok = {(r.get("stage"), str(r.get("seed")), r.get("arm")) for r in ledger if r.get("status") == "ok"}

    def stage_ok(stage: str, seed: object = None, arm: str | None = None) -> bool:
        return (stage, str(seed), arm) in ok

    def find(kind: str, **keys: object) -> list[dict]:
        return [r for r in records if r.get("kind") == kind
                and all(str(r.get(k)) == str(v) for k, v in keys.items())]

    def check(unit: str, reasons: list[str]) -> bool:
        if reasons:
            problems.append(f"{unit}: " + "; ".join(reasons))
        return not reasons

    def failed(*stages: tuple) -> list[str]:
        return [f"stage {s[0]} did not succeed" for s in stages if not stage_ok(*s)]

    def verify_eval(seed: object, arm: str, ckpt: str, step: int, stage: str) -> tuple[dict | None, list[str]]:
        found = find("eval", seed=seed, arm=arm, checkpoint=ckpt)
        reasons = failed((stage, seed, arm))
        if len(found) != 1:
            return None, reasons + [f"{len(found)} evaluation records"]
        rec = found[0]
        if rec.get("step") != step:
            reasons.append(f"evaluated at step {rec.get('step')}, planned {step}")
        if not _file_ok(run_dir, rec):
            return rec, reasons + ["completions file missing or altered"]
        try:
            cases = sorted([c.get("uid"), c.get("role")] for c in read_jsonl(run_dir / rec["file"]))
        except ValueError as exc:
            return rec, reasons + [f"completions file unreadable ({exc})"]
        if cases != expected_cases or sorted(rec.get("completion_digests", {})) != sorted(
                u for u, _ in expected_cases):
            reasons.append("prompt IDs/roles differ from the frozen evaluation and holdout sets")
        return rec, reasons

    check("model and scorer loading", failed(("load_model",), ("load_scorer",)))
    found = find("tokenization")
    reasons = failed(("tokenize",)) + ([] if len(found) == 1 else [f"{len(found)} records"])
    if len(found) == 1 and {r: v.get("n") for r, v in found[0].get("roles", {}).items()} != {
            r: len(u) for r, u in roles.items()}:
        reasons.append("role sizes differ from the frozen manifest")
    tokenization = found[0] if check("tokenization", reasons) else None
    found = find("content_scores")
    reasons = failed(("input_classifier",)) + ([] if len(found) == 1 else [f"{len(found)} records"])
    if len(found) == 1:
        scores = found[0].get("scores", {})
        if sorted(scores) != roles["train"] or not all(_number(p) and 0 <= p <= 1
                                                       for p in scores.values()):
            reasons.append("scores do not cover exactly the frozen training rows with probabilities")
    content = found[0] if check("input classifier", reasons) else None

    evals, fingerprints, attributions, identity = {}, {}, {}, {}
    for seed in plan["seeds"]:
        s = str(seed)
        found = find("checkpoint", seed=seed, arm="init")
        reasons = failed(("init_adapter", seed)) + ([] if len(found) == 1 else [f"{len(found)} records"])
        if len(found) == 1 and (found[0].get("step") != 0 or not _file_ok(run_dir, found[0])):
            reasons.append("not at step 0, or its adapter file is missing or altered")
        init_fp = found[0].get("fingerprint") if check(f"{s}/init", reasons) else None
        starts = {}
        for arm in plan["arms"]:
            found = find("arm_start", seed=seed, arm=arm)
            starts[arm] = found[0].get("init_fingerprint") if len(found) == 1 else None
            trained = [(r.get("step"), r.get("uid")) for r in steps[(s, arm)]]
            planned_uids = plan["streams"][s][arm]["uids"]
            for ckpt, train_stage in (("short", "train_short"), ("long", "train_continue")):
                n = plan[f"{ckpt}_steps"]
                reasons = failed((train_stage, seed, arm))
                if init_fp is None or starts[arm] != init_fp:
                    reasons.append("the arm did not start from the seed's verified initial adapter")
                if (trained[:n] if ckpt == "short" else trained) != list(
                        enumerate(planned_uids[:n], start=1)):
                    reasons.append("trained example IDs differ from the frozen plan")
                found = find("checkpoint", seed=seed, arm=arm, checkpoint=ckpt)
                if len(found) != 1:
                    reasons.append(f"{len(found)} checkpoint records")
                elif (found[0].get("step") != n or found[0].get("init_fingerprint") != init_fp
                      or not _file_ok(run_dir, found[0])):
                    reasons.append(f"checkpoint not at step {n}, not from the initial adapter, "
                                   "or its adapter file is missing or altered")
                rec, why = verify_eval(seed, arm, ckpt, n, f"eval_{ckpt}")
                if check(f"{s}/{arm}/{ckpt}", reasons + why):
                    evals[_key(seed, arm, ckpt)] = rec
                    fingerprints[_key(seed, arm, ckpt)] = found[0].get("fingerprint")
        identity[s] = {"initial_fingerprint": init_fp, "arm_start_fingerprints": starts,
                       "identical_across_arms": init_fp is not None
                       and all(fp == init_fp for fp in starts.values())}
        found = find("attribution", seed=seed)
        reasons = failed(("attribution", seed, "a0")) + ([] if len(found) == 1 else
                                                          [f"{len(found)} records"])
        if len(found) == 1 and (
                found[0].get("step") != plan["long_steps"]
                or sorted(found[0].get("query_uids", [])) != roles["query"]
                or sorted(found[0].get("group_uids", [])) != sorted(plan["removal_uids"])
                or not (_number(found[0].get("cosine_of_means"))
                        and abs(found[0]["cosine_of_means"]) <= 1 + 1e-9)):
            reasons.append("not at the planned a0 step, wrong query or group IDs, or no finite cosine")
        if check(f"{s}/attribution", reasons):
            attributions[s] = found[0]
    if plan["eval_base"]:
        rec, reasons = verify_eval("base", "base", "base", 0, "eval_base")
        if check("base/base/base", reasons):
            evals[_key("base", "base", "base")] = rec
    return {"evals": evals, "fingerprints": fingerprints, "attributions": attributions,
            "identity": identity, "tokenization": tokenization, "content": content}


def summarize(run_dir: str | Path) -> dict:
    """Verify and summarize a run directory. The same function serves the runner's own summary
    and later recoveries; only ``runner_end.json`` decides which one applies."""
    run_dir = Path(run_dir)
    frozen = run_dir / "frozen"
    hashes, plan, config, manifest = (_json(frozen / name) for name in
                                      ("hashes.json", "plan.json", "config.json", MANIFEST_FILE))
    assets = _json(frozen / "assets.json") if (frozen / "assets.json").exists() else None
    end = _json(run_dir / END_FILE) if (run_dir / END_FILE).exists() else None
    frozen_problems = _frozen_problems(frozen, hashes, plan, manifest)
    problems, recovered = list(frozen_problems), []

    def log(rel: str) -> list[dict]:
        """Strict once the runner recorded its end; otherwise (interruption recovery) only an
        unterminated final fragment is dropped, and it is listed. Corruption is a problem."""
        try:
            if end is not None:
                return read_jsonl(run_dir / rel)
            rows, fragment = recover_jsonl(run_dir / rel)
        except ValueError as exc:
            problems.append(f"corrupt log {rel}: {exc}")
            return []
        if fragment:
            recovered.append({"file": rel, "dropped_bytes": len(fragment)})
        return rows

    records, ledger = log("records.jsonl"), log("ledger.jsonl")
    steps = {(str(s), a): log(f"steps/{s}-{a}.jsonl") for s in plan["seeds"] for a in plan["arms"]}
    if end is None:
        status = _json(run_dir / "status.json") if (run_dir / "status.json").exists() else {}
        stop_reason = (f"interrupted: no {END_FILE}, so the runner never recorded its end "
                       f"(status.json last said {status.get('status')!r} at stage "
                       f"{status.get('stage')!r}, {status.get('elapsed_s')} s)")
        termination = "recovered from logs after an interruption (the runner did not end)"
    else:
        stop_reason, termination = end.get("stop_reason"), "runner ended"
    verified = _verify(run_dir, plan, manifest, records, ledger, steps, problems)
    caps, elapsed = config["caps"], None if end is None else end.get("elapsed_s")
    if end is not None and not (_number(elapsed) and elapsed <= caps["wall_seconds"]):
        problems.append(f"runner elapsed {elapsed} s is over the {caps['wall_seconds']} s wall cap "
                        "(a unit overran it)")
    size = output_bytes(run_dir)
    if size > caps["output_bytes"]:
        problems.append(f"outputs {size} bytes are over the {caps['output_bytes']} byte cap")
    errors = [{k: r.get(k) for k in ("stage", "seed", "arm", "status", "seconds", "error")}
              for r in ledger if r.get("status") != "ok"]
    complete = stop_reason is None and not problems and not errors and not recovered
    # The expected units are defined by frozen inputs; invalid inputs cannot verify outcomes.
    evals = {} if frozen_problems else verified["evals"]
    rows, unmatched = matched_comparisons(evals, plan, verified["fingerprints"])
    return {
        "kind": "minimal-safety calibration summary (engineering)",
        "status": "complete" if complete else "incomplete",
        "stop_reason": stop_reason,
        "termination": termination,
        "problems": problems,
        "stage_errors": errors,
        "recovered_fragments": recovered,
        "conclusion": CONCLUSION,
        "disclaimer": disclaimer(plan),
        "identity": {"hashes": hashes, "frozen_verified": not frozen_problems, "assets": assets},
        "caps": {**caps, "runner_elapsed_s": elapsed, "output_bytes_at_summary": size},
        "plan": {**{k: plan[k] for k in ("arms", "seeds", "short_steps", "long_steps",
                                         "removal_uids", "eval_base")},
                 "exposure": {s: {"a0_removed_rows_seen": v["a0"]["removed_seen"],
                                  "first_divergence_step": v["first_divergence_step"]}
                              for s, v in plan["streams"].items()}},
        "evals": [evals[k] for k in sorted(evals)],
        "comparisons": {"basis": ("descriptive differences on verified (seed, checkpoint) pairs "
                                  "at the planned step only" + ("" if complete else "; PARTIAL RUN")),
                        "rows": rows, "unmatched": unmatched},
        "attribution": [verified["attributions"][k] for k in sorted(verified["attributions"])],
        "content_scores": (content_summary(verified["content"], plan)
                           if verified["content"] else None),
        "tokenization": verified["tokenization"],
        "init_identity": verified["identity"],
        "checkpoints": [r for r in records if r.get("kind") == "checkpoint"],
        "costs": stage_costs(ledger, plan),
        "elapsed_s": elapsed,
        "audit": export_audit(run_dir, list(evals.values()), plan["audit_shuffle_seed"]),
    }


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _table(header: list[str], rows: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    return lines + ["| " + " | ".join(_fmt(v) for v in row) + " |" for row in rows]


def render_report(summary: dict) -> str:
    s = summary
    status = s["status"].upper() + (f" ({s['stop_reason']})" if s["stop_reason"] else "")
    hashes = s["identity"]["hashes"]
    out = ["# Minimal safety calibration: run report", "", f"**Status: {status}**", "",
           f"Termination: {s['termination']}", "",
           f"Conclusion: {s['conclusion']}", "", f"> {s['disclaimer']}", "",
           "## Identity", "",
           f"- config sha256 `{hashes.get('config')}`; manifest sha256 `{hashes.get('manifest')}`; "
           f"plan sha256 `{hashes.get('plan')}`; frozen files recomputed and matching: "
           f"{'yes' if s['identity']['frozen_verified'] else 'NO'}"]
    assets = s["identity"]["assets"] or {}
    for name in ("model", "scorer"):
        if name in assets:
            out.append(f"- {name} `{assets[name].get('repo_id')}@{assets[name].get('revision')}`")
    if "device" in assets:
        out.append(f"- device `{assets['device']}`")
    caps = s["caps"]
    out.append(f"- caps: wall {caps['wall_seconds']} s (runner elapsed {_fmt(caps['runner_elapsed_s'])} s);"
               f" outputs {caps['output_bytes']} bytes ({caps['output_bytes_at_summary']} at summary)")
    plan = s["plan"]
    out += ["", "## Plan", "",
            f"- arms {plan['arms']}; seeds {plan['seeds']}; steps {plan['short_steps']}/"
            f"{plan['long_steps']}; removal group {len(plan['removal_uids'])} rows",
            *[f"- seed {seed}: a0 saw {v['a0_removed_rows_seen']} removal-group rows "
              f"(short/long); first data divergence at step {_fmt(v['first_divergence_step'])}"
              for seed, v in plan["exposure"].items()]]
    if s["problems"] or s["stage_errors"] or s["recovered_fragments"]:
        out += ["", "## Problems, stopped stages and recovered logs", "",
                *[f"- problem: {p}" for p in s["problems"]],
                *[f"- stage {e['stage']} (seed {_fmt(e['seed'])}, arm {_fmt(e['arm'])}): "
                  f"{e['status']} after {_fmt(e['seconds'])} s: {e['error']}" for e in s["stage_errors"]],
                *[f"- recovered: dropped an unterminated final fragment ({r['dropped_bytes']} bytes) "
                  f"of {r['file']}" for r in s["recovered_fragments"]]]
    tok = s["tokenization"]
    if tok:
        out += ["", "## Tokenization", "",
                *[f"- {role}: {v['n']} rows, prompt truncated {v['prompt_truncated']}, response "
                  f"truncated {v['response_truncated']}, max {v['max_tokens']} tokens"
                  for role, v in tok["roles"].items()],
                f"- prompts checked against the canonical chat template: "
                f"{_fmt(tok.get('template_checked_prompts'))}; responses starting with whitespace: "
                f"{_fmt(tok.get('responses_with_leading_whitespace'))}"]
    out += ["", "## Verified evaluations (classifier proxy and diagnostics)", ""]
    out += _table(["seed", "arm", "ckpt", "step", "toxic proxy rate", "mean p_toxic",
                   "toxic-ref NLL", "benign NLL", "benign refusal flags", "empty", "copy flags",
                   "mean new tokens (toxic/benign)", "hit token cap"],
                  [[e["seed"], e["arm"], e["checkpoint"], e["step"], e["toxic"]["proxy_rate"],
                    e["toxic"]["mean_p_toxic"], e["toxic_ref_nll_mean"], e["benign"]["mean_nll"],
                    e["benign"]["refusal_flags"], e["toxic"]["empty"] + e["benign"]["empty"],
                    e["toxic"]["copy_flags"] + e["benign"]["copy_flags"],
                    f"{_fmt(e['toxic']['mean_new_tokens'])}/{_fmt(e['benign']['mean_new_tokens'])}",
                    e["toxic"]["hit_max_new_tokens"] + e["benign"]["hit_max_new_tokens"]]
                   for e in s["evals"]])
    comp = s["comparisons"]
    out += ["", f"## Matched descriptive differences ({comp['basis']})", ""]
    out += _table(["seed", "ckpt", "step", "sign", "d proxy rate", "d mean p_toxic",
                   "d toxic-ref NLL", "d benign NLL", "identical completions",
                   "a0 removal rows seen", "first divergence", "data identical",
                   "adapters identical"],
                  [[r["seed"], r["checkpoint"], r["step"], r["sign"], r["delta_toxic_proxy_rate"],
                    r["delta_toxic_mean_p"], r["delta_toxic_ref_nll"], r["delta_benign_nll"],
                    f"{r['identical_completions']}/{r['compared_completions']}",
                    r["a0_removed_rows_seen"], r["first_divergence_step"], r["data_identical"],
                    r["adapters_identical"]]
                   for r in comp["rows"]])
    out += [f"- unmatched: seed {u['seed']} {u['checkpoint']}: {'; '.join(u['reasons'])}"
            for u in comp["unmatched"]]
    out += [f"- seed {r['seed']} {r['checkpoint']}: identical data, initial adapter and fresh "
            "optimizer, yet the adapters differ: investigate an implementation difference or "
            "numerical nondeterminism before reading any difference in this run"
            for r in comp["rows"] if r["data_identical"] and r["adapters_identical"] is False]
    out += ["", "## Gradient cosine at a0 long (noncausal diagnostic)", ""]
    out += _table(["seed", "cosine of mean gradients", "per-example min", "per-example max",
                   "query mean-grad norm", "group mean-grad norm"],
                  [[a["seed"], a["cosine_of_means"], min(a["per_example_cosine"].values()),
                    max(a["per_example_cosine"].values()), a["query_mean_grad_norm"],
                    a["group_mean_grad_norm"]] for a in s["attribution"]])
    if s["content_scores"]:
        c = s["content_scores"]
        out += ["", "## Input classifier on training responses (proxy)", "",
                f"- removal group: n {c['removal_group']['n']}, mean p_toxic "
                f"{_fmt(c['removal_group']['mean_p_toxic'])}, flagged {c['removal_group']['flagged']}",
                f"- retained rows: n {c['retained']['n']}, mean p_toxic "
                f"{_fmt(c['retained']['mean_p_toxic'])}, flagged {c['retained']['flagged']}"]
    costs = s["costs"]
    out += ["", "## Costs (seconds, synchronized stage wall time, successful stages only)", "",
            *[f"- {k}: {_fmt(v)}" for k, v in costs["one_off"].items()],
            f"- base evaluation: {_fmt(costs['eval_base'])}", ""]
    out += _table(["seed", "adapter init", "attribution (a0 long)"],
                  [[seed, v["init_adapter"], v["attribution"]]
                   for seed, v in costs["per_seed"].items()])
    out += [""]
    out += _table(["seed/arm", "train short", "eval short", "train continue", "eval long",
                   "full-run train", "full run", "selector path", "s/step"],
                  [[k, v["train_short"], v["eval_short"], v["train_continue"], v["eval_long"],
                    v["full_run_train"], v["full_run"], v["selector_path"], v["seconds_per_step"]]
                   for k, v in costs["per_arm"].items()])
    if costs["stopped"]:
        out += ["", f"Spent on stopped stages (not completed units; excluded above): "
                    f"{_fmt(costs['stopped_seconds'])} s", "",
                *[f"- {r['stage']} (seed {_fmt(r['seed'])}, arm {_fmt(r['arm'])}): {r['status']}, "
                  f"{_fmt(r['seconds'])} s spent, stopped at '{_fmt(r['last_item'])}'; "
                  f"{r['error']}" for r in costs["stopped"]]]
    out += ["", f"- sum of all stages {_fmt(costs['sum_of_stage_seconds'])} s; outside stages "
                f"{_fmt(costs['outside_stages_s'])} s; runner elapsed {_fmt(s['elapsed_s'])} s",
            "", *[f"- {k}: {v}" for k, v in costs["definitions"].items()],
            "", "## Initialization identity", "",
            *[f"- seed {seed}: arms started from the verified initial adapter = "
              f"{v['identical_across_arms']}" for seed, v in s["init_identity"].items()],
            "", "## Audit", "",
            f"- {s['audit']['items']} blind items ({s['audit']['cases']} cases) in "
            f"`{s['audit']['blind_file']}`; mapping in `{s['audit']['mapping_file']}`; "
            f"{s['audit']['status']}", ""]
    return "\n".join(out)


def finalize(run_dir: str | Path, write_status: bool = True) -> dict:
    """Write summary.json and report.md (and, for the runner, the final status.json)."""
    run_dir = Path(run_dir)
    summary = summarize(run_dir)
    write_json(run_dir / "summary.json", summary)
    write_atomic(run_dir / "report.md", render_report(summary).encode("utf-8"))
    if write_status:
        write_json(run_dir / "status.json", {"status": summary["status"],
                                             "stop_reason": summary["stop_reason"],
                                             "elapsed_s": summary["elapsed_s"],
                                             "problems": summary["problems"]})
    return summary
