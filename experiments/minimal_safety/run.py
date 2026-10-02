"""One calibration run. Order of work:

1. freeze: copy config, manifest and rows into ``frozen/`` and write the exact per-step data
   streams (``plan.json``) and hashes BEFORE any model is loaded;
2. load the pinned assets, tokenize every row (truncations recorded; every prompt checked
   against the tokenizer's canonical chat-template encoding), score training responses with
   the input classifier;
3. per seed (seed-major, so the first seed's pair completes first): initialize the seeded
   adapter once, then for each arm restore that exact adapter, build a fresh optimizer, train
   steps 1..short, checkpoint, evaluate, continue to long, checkpoint, evaluate; after a0,
   compute the gradient cosine on the a0-long model;
4. optionally evaluate the base model (adapter B = 0) last;
5. check both caps once more, write ``runner_end.json`` (the runner's own end: stop reason and
   elapsed time) and summarize. Any cap, error or interrupt still produces
   ``summary.json``/``report.md`` with status ``incomplete``; nothing is resumed and no arm is
   shortened to fit the cap. A run killed before step 5 has no ``runner_end.json``;
   ``summarize`` then recovers it as interrupted.

Caps are cooperative: every stage entry, arm start, optimizer step, generated token,
teacher-forced NLL, classifier batch, per-example gradient and file save is preceded by a
check. One operation already in progress (a model load, a forward/backward pass, a decoding
step, a classifier batch, a checkpoint write) can still finish past the cap; the final check
and the recorded elapsed time then make the run incomplete rather than hiding the overshoot.
"""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Callable

from . import data, report
from . import model as tm
from .common import append_jsonl, sha256_bytes, write_atomic, write_json
from .ledger import CapExceeded, Ledger
from .plan import arms, code_hashes, config_sha256, load_config, validate
from .text import copy_fraction, encode_example, encode_prompt, refusal_flag

__all__ = ["RunError", "freeze", "Calibration", "execute", "main_run"]


class RunError(RuntimeError):
    """The run cannot start (inputs not frozen or inconsistent) or an invariant broke."""


def freeze(config: dict, prepared_dir: str | Path, run_dir: str | Path,
           manifest_sha256: str) -> dict:
    run_dir = Path(run_dir)
    if run_dir.exists() and any(run_dir.iterdir()):
        raise RunError(f"{run_dir} is not empty: runs are never resumed or overwritten")
    manifest, rows, digest = data.load_prepared(prepared_dir, manifest_sha256)
    if manifest["config_dataset"] != config["dataset"] or manifest["config_design"] != config["design"]:
        raise RunError("prepared data were built from a different dataset/design config")
    manifest_bytes = (Path(prepared_dir) / data.MANIFEST_FILE).read_bytes()
    rows_bytes = (Path(prepared_dir) / manifest["rows_file"]).read_bytes()
    if sha256_bytes(manifest_bytes) != digest or sha256_bytes(rows_bytes) != manifest["rows_sha256"]:
        raise RunError("prepared files changed while freezing")
    train, ev = config["train"], config["eval"]
    plan = {"config_sha256": config_sha256(config), "manifest_sha256": digest, "arms": arms(config),
            "seeds": train["seeds"], "short_steps": train["short_steps"],
            "long_steps": train["long_steps"], "removal_uids": manifest["removal_group"]["uids"],
            "removal_label": manifest["removal_group"]["label"],
            "streams": data.stream_plan(manifest, config), "eval_base": ev["eval_base"],
            "toxic_threshold": ev["toxic_threshold"],
            "audit_shuffle_seed": config["audit"]["shuffle_seed"]}
    folder = run_dir / "frozen"
    write_atomic(folder / data.MANIFEST_FILE, manifest_bytes)
    write_atomic(folder / data.ROWS_FILE, rows_bytes)
    hashes = {"config": write_json(folder / "config.json", config), "manifest": digest,
              "rows": manifest["rows_sha256"], "plan": write_json(folder / "plan.json", plan),
              "code": code_hashes()}
    write_json(folder / "hashes.json", hashes)
    return {"plan": plan, "rows": rows}


def _mean(values) -> float | None:
    values = list(values)
    return sum(values) / len(values) if values else None


def _group(cases: list[dict]) -> dict:
    flagged = sum(c["toxic_flag"] for c in cases)
    return {"n": len(cases), "flagged": flagged,
            "proxy_rate": flagged / len(cases) if cases else None,
            "mean_p_toxic": _mean(c["p_toxic"] for c in cases),
            "mean_nll": _mean(c["reference_nll"] for c in cases),
            "empty": sum(c["empty"] for c in cases),
            "refusal_flags": sum(c["refusal_flag"] for c in cases),
            "copy_flags": sum(c["copy_flag"] for c in cases),
            "mean_new_tokens": _mean(c["new_tokens"] for c in cases),
            "hit_max_new_tokens": sum(not c["stopped"] for c in cases),
            "prompt_truncated": sum(c["prompt_truncated"] for c in cases)}


class Calibration:
    def __init__(self, config: dict, frozen: dict, assets: tm.Assets, ledger: Ledger,
                 run_dir: Path) -> None:
        self.config, self.plan, self.assets, self.ledger = config, frozen["plan"], assets, ledger
        self.run_dir = Path(run_dir)
        self.rows = {role: [r for r in frozen["rows"] if r["role"] == role] for role in data.ROLES}
        self.eval_seconds: list[float] = []

    def record(self, **fields: object) -> None:
        append_jsonl(self.run_dir / "records.jsonl", fields)

    def tick(self, what: str) -> None:
        """Fine-grained cooperative wall-cap check before one work item (no directory walk)."""
        self.ledger.check(0.0, what, outputs=False)

    def score(self, texts: list[str], what: str) -> list[float]:
        """Classifier probabilities in config-sized batches, with a cap check before each."""
        size, out = self.config["scorer"]["batch_size"], []
        for start in range(0, len(texts), size):
            self.tick(f"{what} classifier batch {start // size + 1}")
            out += self.assets.score(texts[start:start + size])
        return out

    def _rel(self, path: Path) -> str:
        return str(path.relative_to(self.run_dir))

    def run(self) -> None:
        self.tokenize()
        self.classify_inputs()
        previous = 0.0
        for seed in self.plan["seeds"]:
            init, fingerprint = self.init_adapter(seed)
            for arm in self.plan["arms"]:
                # Do not start an arm the cap cannot accommodate (predicted by the last arm's
                # training and evaluation time; attribution is timed separately).
                self.ledger.check(previous, f"seed {seed} arm {arm}")
                start = self.ledger.elapsed()
                step = self.train_arm(seed, arm, init, fingerprint)
                previous = self.ledger.elapsed() - start
                if arm == self.config["attribution"]["arm"]:
                    self.attribute(seed, step)
        if self.plan["eval_base"]:
            self.ledger.check(max(self.eval_seconds, default=0.0), "base evaluation")
            named = self.assets.named
            tm.load_lora_state(named, tm.init_lora_state(named, self.plan["seeds"][0]))  # B = 0
            self.evaluate("base", "base", "base", 0, "eval_base")

    def check_template(self) -> int | None:
        """How many frozen prompts were checked: each untruncated prompt encoding must equal the
        tokenizer's canonical chat-template encoding, or the run stops. None for fixture codecs
        that have no reference encoding."""
        codec = self.assets.codec
        if codec.reference is None:
            return None
        rows = [r for role in data.ROLES for r in self.rows[role]]
        bad = [r["uid"] for r in rows
               if codec.encode_turn(r["prompt"]) + list(codec.tail_ids) != codec.reference(r["prompt"])]
        if bad:
            raise RunError(f"{len(bad)} prompt(s) differ from the canonical chat-template "
                           f"encoding: {bad[:5]}")
        return len(rows)

    def tokenize(self) -> None:
        train, ev, codec = self.config["train"], self.config["eval"], self.assets.codec
        max_len, reserve = train["max_seq_len"], train["reserved_response_tokens"]
        cap = max_len - ev["max_new_tokens"]
        with self.ledger.stage("tokenize") as info:
            checked = self.check_template()
            self.examples = {role: [encode_example(codec, r["uid"], r["prompt"], r["response"],
                                                   max_len, reserve) for r in self.rows[role]]
                             for role in data.ROLES}
            self.prompts = {role: [encode_prompt(codec, r["prompt"], cap) for r in self.rows[role]]
                            for role in ("eval", "holdout")}
            info.update(examples=sum(len(v) for v in self.examples.values()),
                        template_checked=checked)
        self.train_ex = {e.uid: e for e in self.examples["train"]}
        roles = {role: {"n": len(items),
                        "prompt_truncated": sum(e.prompt_truncated for e in items),
                        "response_truncated": sum(e.response_truncated for e in items),
                        "mean_tokens": _mean(len(e.input_ids) for e in items),
                        "max_tokens": max((len(e.input_ids) for e in items), default=0),
                        "target_tokens": sum(e.n_target for e in items)}
                 for role, items in self.examples.items()}
        prompts = {role: {"n": len(items), "prompt_truncated": sum(t for _, t in items),
                          "max_tokens": max((len(ids) for ids, _ in items), default=0)}
                   for role, items in self.prompts.items()}
        self.record(kind="tokenization", roles=roles, generation_prompts=prompts,
                    max_seq_len=max_len, reserved_response_tokens=reserve,
                    generation_prompt_cap=cap, template_checked_prompts=checked,
                    responses_with_leading_whitespace=sum(
                        r["response"][:1].isspace() for rows in self.rows.values() for r in rows))

    def classify_inputs(self) -> None:
        texts = [r["response"] for r in self.rows["train"]]
        with self.ledger.stage("input_classifier") as info:
            scores = self.score(texts, "input_classifier")
            truncated = self.assets.count_truncated(texts)
            info.update(texts=len(texts), truncated=truncated)
        self.record(kind="content_scores", target="training responses",
                    threshold=self.plan["toxic_threshold"], n_truncated=truncated,
                    scores={r["uid"]: p for r, p in zip(self.rows["train"], scores, strict=True)})

    def init_adapter(self, seed: int) -> tuple[dict, str]:
        named = self.assets.named
        path = self.run_dir / "adapters" / f"{seed}-init.safetensors"
        with self.ledger.stage("init_adapter", seed=seed) as info:
            state = tm.init_lora_state(named, seed)
            tm.load_lora_state(named, state)
            fingerprint = tm.lora_fingerprint(named)
            digest = tm.save_lora(named, path, {"seed": seed, "step": 0, "kind": "initial (B = 0)"})
            info.update(fingerprint=fingerprint)
        self.record(kind="checkpoint", seed=seed, arm="init", checkpoint="init", step=0,
                    file=self._rel(path), sha256=digest, fingerprint=fingerprint)
        return state, fingerprint

    def train_arm(self, seed: int, arm: str, init: dict, fingerprint: str) -> int:
        assets, train = self.assets, self.config["train"]
        tm.load_lora_state(assets.named, init)
        if tm.lora_fingerprint(assets.named) != fingerprint:
            raise RunError(f"seed {seed} arm {arm}: adapter differs from the seed's initial adapter")
        self.record(kind="arm_start", seed=seed, arm=arm, init_fingerprint=fingerprint)
        optimizer = tm.make_optimizer(assets.named, train)  # fresh state for every arm
        stream = self.plan["streams"][str(seed)][arm]["uids"]
        group = set(self.plan["removal_uids"])
        removed = group if arm != "a0" else set()
        steps_path = self.run_dir / "steps" / f"{seed}-{arm}.jsonl"
        step, totals = 0, {"input_tokens": 0, "target_tokens": 0, "removal_rows_seen": 0}
        for ckpt, upto, stage in (("short", train["short_steps"], "train_short"),
                                  ("long", train["long_steps"], "train_continue")):
            path = self.run_dir / "adapters" / f"{seed}-{arm}-step{upto}.safetensors"
            with self.ledger.stage(stage, seed=seed, arm=arm) as info:
                before = dict(totals)
                info.update(first_step=step + 1)  # progress stays in the ledger if interrupted
                while step < upto:
                    self.ledger.check(0.0, f"{stage} step {step + 1} (seed {seed}, {arm})")
                    uid = stream[step]
                    if uid in removed:
                        raise RunError(f"removed row {uid} reached the sampler")
                    example = self.train_ex[uid]
                    start = self.ledger.elapsed()
                    out = tm.train_step(assets.model, assets.named, optimizer, example,
                                        train["max_grad_norm"], assets.device)
                    step += 1
                    totals["input_tokens"] += len(example.input_ids)
                    totals["target_tokens"] += example.n_target
                    totals["removal_rows_seen"] += uid in group
                    append_jsonl(steps_path, {"step": step, "uid": uid,
                                              "input_tokens": len(example.input_ids),
                                              "target_tokens": example.n_target,
                                              "seconds": self.ledger.elapsed() - start, **out})
                    info.update(last_step=step, **{k: totals[k] - before[k] for k in totals})
                self.ledger.check(0.0, f"saving {path.name}")
                digest = tm.save_lora(assets.named, path, {"seed": seed, "arm": arm, "step": step})
            self.record(kind="checkpoint", seed=seed, arm=arm, checkpoint=ckpt, step=step,
                        file=self._rel(path), sha256=digest,
                        fingerprint=tm.lora_fingerprint(assets.named),
                        init_fingerprint=fingerprint, uids=stream[:step], **totals)
            self.evaluate(seed, arm, ckpt, step, f"eval_{ckpt}")
        optimizer.zero_grad(set_to_none=True)
        return step

    def evaluate(self, seed: object, arm: str, ckpt: str, step: int, stage: str) -> None:
        assets, ev = self.assets, self.config["eval"]
        rows = self.rows["eval"] + self.rows["holdout"]
        prompts = self.prompts["eval"] + self.prompts["holdout"]
        start = self.ledger.elapsed()
        with self.ledger.stage(stage, seed=seed, arm=arm) as info:
            generations, nlls = tm.generate_and_nll(
                assets.model, [ids for ids, _ in prompts],
                self.examples["eval"] + self.examples["holdout"], ev["max_new_tokens"],
                assets.codec.stop_ids, assets.device,
                check=lambda what: self.tick(f"{stage} {what}"))
            texts = [assets.codec.decode(ids) for ids, _ in generations]
            scored_at = self.ledger.elapsed()
            scores = self.score(texts, stage)
            scorer_seconds = self.ledger.elapsed() - scored_at
            cases = []
            for row, (prompt_ids, cut), (ids, stopped), text, p, nll in zip(
                    rows, prompts, generations, texts, scores, nlls, strict=True):
                fraction = copy_fraction(row["prompt"], text, ev["copy_ngram"])
                cases.append({"uid": row["uid"], "role": row["role"], "prompt": row["prompt"],
                              "completion": text, "new_tokens": len(ids), "stopped": stopped,
                              "prompt_tokens": len(prompt_ids), "prompt_truncated": cut,
                              "empty": not text.strip(), "p_toxic": p,
                              "toxic_flag": p >= ev["toxic_threshold"],
                              "refusal_flag": refusal_flag(text), "copy_fraction": fraction,
                              "copy_flag": fraction is not None and fraction >= ev["copy_fraction"],
                              "reference_nll": nll})
            path = self.run_dir / "completions" / f"{seed}-{arm}-{ckpt}.jsonl"
            payload = "".join(json.dumps(c, sort_keys=True, ensure_ascii=False) + "\n"
                              for c in cases).encode("utf-8")
            self.ledger.check(0.0, f"saving {path.name}")
            write_atomic(path, payload)
            info.update(generated_tokens=sum(c["new_tokens"] for c in cases),
                        prompt_tokens=sum(c["prompt_tokens"] for c in cases),
                        scorer_seconds=scorer_seconds)
        self.eval_seconds.append(self.ledger.elapsed() - start)
        toxic = [c for c in cases if c["role"] == "eval"]
        self.record(kind="eval", seed=seed, arm=arm, checkpoint=ckpt, step=step,
                    toxic=_group(toxic), benign=_group([c for c in cases if c["role"] == "holdout"]),
                    toxic_ref_nll_mean=_mean(c["reference_nll"] for c in toxic),
                    generated_tokens=sum(c["new_tokens"] for c in cases),
                    scorer_seconds=scorer_seconds, file=self._rel(path),
                    sha256=sha256_bytes(payload),
                    completion_digests={c["uid"]: sha256_bytes(c["completion"].encode("utf-8"))[:16]
                                        for c in cases})

    def attribute(self, seed: int, step: int) -> None:
        group = [self.train_ex[u] for u in self.plan["removal_uids"]]
        queries = self.examples["query"]
        try:
            with self.ledger.stage("attribution", seed=seed, arm="a0") as info:
                result = tm.query_group_cosine(self.assets.model, self.assets.named, queries, group,
                                               self.assets.device,
                                               check=lambda what: self.tick(f"attribution {what}"))
                info.update(examples=len(group) + len(queries),
                            tokens=sum(len(e.input_ids) for e in group + queries))
        except (tm.NonFiniteError, tm.ZeroGradientError) as exc:
            # Recorded as a failed unit (the ledger has the error); training continues.
            self.record(kind="attribution_failed", seed=seed, error=f"{type(exc).__name__}: {exc}")
            return
        self.record(kind="attribution", seed=seed, arm="a0", checkpoint="long", step=step,
                    query_uids=[e.uid for e in queries], group_uids=[e.uid for e in group], **result)


def execute(config: dict, prepared_dir: str | Path, run_dir: str | Path, manifest_sha256: str,
            load_assets: Callable[[dict, Ledger], tm.Assets], *,
            clock: Callable[[], float] = time.monotonic, sync: Callable[[], None] | None = None,
            memory: Callable[[], dict] | None = None) -> dict:
    validate(config)
    run_dir = Path(run_dir)
    frozen = freeze(config, prepared_dir, run_dir, manifest_sha256)
    caps = config["caps"]
    ledger = Ledger(run_dir, caps["wall_seconds"], caps["output_bytes"], clock=clock, sync=sync,
                    memory=memory)
    ledger.status("running", stage="start")
    stop_reason = None
    try:
        assets = load_assets(config, ledger)
        write_json(run_dir / "frozen" / "assets.json", assets.identity)
        Calibration(config, frozen, assets, ledger, run_dir).run()
        ledger.check(0.0, "completion (final check after the last unit)")
    except CapExceeded as exc:
        stop_reason = f"cap: {exc}"
    except KeyboardInterrupt:
        stop_reason = "interrupted (KeyboardInterrupt)"
    except Exception as exc:  # noqa: BLE001 - every failure is recorded and summarized
        stop_reason = f"error: {type(exc).__name__}: {exc}"
        write_atomic(run_dir / "error.txt", traceback.format_exc().encode("utf-8"))
    # Written once, only here: the evidence that the runner ended (successfully or with a
    # caught stop) rather than being killed. Summaries without it are interruption recoveries.
    write_json(run_dir / report.END_FILE, {"stop_reason": stop_reason, "elapsed_s": ledger.elapsed()})
    ledger.status("finalizing", stop_reason=stop_reason)
    return report.finalize(run_dir)


def main_run(config_path: str, prepared_dir: str, run_dir: str, manifest_sha256: str) -> dict:
    config = load_config(config_path)
    sync, memory = tm.device_hooks(config["model"]["device"])
    return execute(config, prepared_dir, run_dir, manifest_sha256, tm.load_assets, sync=sync,
                   memory=memory)
