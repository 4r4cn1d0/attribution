"""ENGINEERING FIXTURE: a synthetic world and a fake backend with the controller's backend
interface, for policy-semantics tests and the ``simulate`` exercise. Deterministic outcomes
(seeded, with common random numbers across arms of one seed), scripted durations, overruns,
failures, exceptions after work, validation refusals and arm-dependent final failures, and a
fake clock. Nothing here is a scientific result or stands in for one.

Every evaluation draws per-item labels, refusal answers and capped, empty and repetitive flags
and tallies them with ``outcomes.tally_generations``, so raw flags, missing-label and broader
intervals and diagnostics follow the same definition as engine evaluations. The fake backend
writes one canonical ``artifact.json`` per operation and reads it back with hash checks; the
selector view and relevance table it writes go through the real strict readers; final
operations need the choice lock exactly as with the engine.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from experiments.safety_selection.selector_view import VIEW_KIND, read_selector_view, validate_view

from .backend import check_lock
from .common import (PolicyError, RequestRefused, VerificationError, canonical_json, derive_seed,
                     engine_code_identity, policy_code_identity, read_canonical, sha256_bytes, write_once)
from .config import EXAMPLE_STATUS
from .costs import Shape
from .development import fit_record, table_from_parts
from .features import ATTRIBUTION_NAMES, CATALOGUE_SHA256, TARGETS, view_features
from .outcomes import OUTCOME_PIN, Evaluation, evaluation_from_counts, paired_change, tally_generations
from .tfidf import DEFINITION_SHA256, FEATURES as RELEVANCE_FEATURES, TABLE_KIND, read_relevance

__all__ = ["FIXTURE", "SyntheticWorld", "FakeBackend", "make_world", "prepare_synthetic", "synthetic_pins",
           "SYNTHETIC_RECIPE", "SYNTHETIC_DATA_CONFIG", "evaluation_from_artifact"]

FIXTURE = "ENGINEERING FIXTURE (synthetic; not a scientific result)"
EPOCHS = {"init": 0.0, "q": 0.25, "e1": 1.0, "e3": 3.0}
MAX_NEW_TOKENS = 128


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _generations(rng: random.Random, n: int, *, unsafe: float, refusal: float, rates: Mapping[str, float]) -> dict:
    """Counts of ``n`` synthetic generations; the same number of draws per item whatever the
    probabilities, so arms of one seed share their uniforms (paired items)."""
    items = []
    for _ in range(n):
        u_label, u_controversial, u_invalid, u_refusal, u_capped, u_empty, u_repetitive = (rng.random() for _ in range(7))
        capped = u_capped < rates["capped"]
        empty = not capped and u_empty < rates["empty"]
        tokens = MAX_NEW_TOKENS if capped else 0 if empty else 1 + int(u_empty * (MAX_NEW_TOKENS - 2))
        if u_invalid < rates["invalid"]:
            label, answer = "invalid", None
        else:
            label = ("Unsafe" if u_label < unsafe else
                     "Controversial" if u_controversial < rates["controversial"] else "Safe")
            answer = "Yes" if u_refusal < refusal else "No"
        items.append((label, answer, capped, empty, u_repetitive < rates["repetitive"], tokens))
    return tally_generations(items)


def _forced_choice(rng: random.Random, n: int, accuracy: float) -> dict:
    """Counts of ``n`` synthetic forced-choice items (two-way ties; 2% contain the answer)."""
    correct = ties = answer_ties = 0
    for _ in range(n):
        u_correct, u_tie = rng.random(), rng.random()
        if u_correct < accuracy:
            correct += 1
        elif u_tie < 0.03:
            ties += 1
            answer_ties += int(u_tie < 0.02)
    return {"n": n, "correct": correct, "ties": ties, "answer_ties": answer_ties,
            "expected_correct": correct + 0.5 * answer_ties}


@dataclass
class SyntheticWorld:
    """Per split, group id -> (size, (dF, L, O) full-checkpoint mean change)."""

    seed: int
    groups: Mapping[str, Mapping[str, tuple[int, tuple[float, float, float]]]]
    corpus_rows: int = 10000
    queries: int = 30
    noise: float = 0.03
    fraction: Mapping[str, float] = field(default_factory=lambda: {"init": 0.0, "q": 0.25, "e1": 0.6, "e3": 1.0})
    banks: Mapping[str, tuple[int, int, int]] = field(
        default_factory=lambda: {"dev": (72, 64, 128), "selector": (80, 64, 128), "hidden": (143, 64, 128)})
    durations: Mapping[str, float] = field(default_factory=lambda: {
        "screen": 100.0, "full_from_short": 300.0, "full_from_init": 400.0, "extend": 200.0,
        "attribution": 150.0, "final": 450.0, "score_groups": 50.0, "export_view": 1.0, "relevance": 20.0})
    item_rates: Mapping[str, float] = field(default_factory=lambda: {
        "invalid": 0.02, "controversial": 0.04, "capped": 0.04, "empty": 0.01, "repetitive": 0.03})
    overrun: Mapping[str, float] = field(default_factory=dict)
    failures: frozenset = frozenset()          # (op_id, attempt): a returned technical failure
    interrupts: frozenset = frozenset()        # (op_id, attempt): KeyboardInterrupt midway
    raises: Mapping = field(default_factory=dict)  # (op_id, attempt) -> message: an exception after the work
    refusals: frozenset = frozenset()          # (op_id, attempt): a validation refusal before any work
    final_failures: frozenset = frozenset()    # arms whose final deployment fails at every attempt
    session_setup_seconds: float = 30.0

    def edits(self, split: str) -> tuple[str, ...]:
        return tuple(sorted(self.groups[split]))

    def shape(self, split: str, attribution_checkpoints=("q", "e1", "e3")) -> Shape:
        examples = {"a0": {c: int(EPOCHS[c] * self.corpus_rows) for c in EPOCHS}}
        for gid, (size, _) in self.groups[split].items():
            examples[gid] = {c: int(EPOCHS[c] * (self.corpus_rows - size)) for c in EPOCHS}
        members = sum(size for size, _ in self.groups[split].values())
        return Shape(tuple(EPOCHS), examples, tuple(attribution_checkpoints),
                     (members + self.queries) * len(attribution_checkpoints), members, self.edits(split))

    def evaluation(self, *, split: str, role: str, arm: str, seed: int, checkpoint: str, bank: str) -> dict:
        n_s, n_g, n_u = self.banks[bank]
        common = random.Random(derive_seed("world-common", self.seed, seed, checkpoint, bank))
        own = random.Random(derive_seed("world-arm", self.seed, arm, seed, checkpoint, bank))
        frac = self.fraction[checkpoint]
        d_f, d_l, d_o = (0.0, 0.0, 0.0) if arm == "a0" else self.groups[split][arm][1]
        f = _clamp(0.30 + common.gauss(0, self.noise) + frac * d_f + own.gauss(0, self.noise / 2))
        u = _clamp(0.70 + common.gauss(0, self.noise) - frac * d_l + own.gauss(0, self.noise / 2))
        r = _clamp(0.05 + common.gauss(0, self.noise / 2) + frac * d_o + own.gauss(0, self.noise / 4))
        nll = 1.2 - 0.2 * frac + common.gauss(0, 0.01) + 0.5 * frac * d_f + own.gauss(0, 0.005)
        counts = {"safety": _generations(common, n_s, unsafe=f, refusal=0.3, rates=self.item_rates),
                  "arc_generation": _generations(common, n_g, unsafe=0.01, refusal=r, rates=self.item_rates),
                  "arc_utility": _forced_choice(common, n_u, u)}
        return {"counts": counts, "query_nll": nll,
                "pairing": {"world": self.seed, "split": split, "role": role, "seed": seed,
                            "checkpoint": checkpoint, "bank": bank}}

    def attribution(self, split: str, seed: int) -> dict:
        rng = random.Random(derive_seed("world-attribution", self.seed, split, seed))
        return {gid: {ATTRIBUTION_NAMES[0]: -5.0 * eff[0] + rng.gauss(0, 0.05),
                      ATTRIBUTION_NAMES[1]: -0.1 * eff[0] + rng.gauss(0, 0.002)}
                for gid, (_, eff) in sorted(self.groups[split].items())}

    def view(self, split: str) -> dict:
        rng = random.Random(derive_seed("world-view", self.seed, split))
        ids = self.edits(split)
        ranks = list(range(len(ids)))
        rng.shuffle(ranks)
        groups = {}
        for gid, rank in zip(ids, ranks):
            size, (d_f, _, _) = self.groups[split][gid]
            toxic = max(0, min(size, round(size * (0.25 + 2 * max(0.0, -d_f)))))
            unsafe = min(toxic, rng.randint(0, toxic))
            summary = lambda base: {"sum": base * size, "mean": float(base), "min": base // 2, "max": base * 2}  # noqa: E731
            scored = size
            groups[gid] = {
                "static": {"size": size, "tie_rank": rank, "provenance": {"ToxicChat": toxic, "UltraChat": size - toxic},
                           "chars": summary(900), "response_chars": summary(600), "tokens": summary(250),
                           "target_tokens": summary(160)},
                "guard": {"size": size, "guard_invalid": 0, "guard_unsafe": unsafe, "guard_controversial": 0,
                          "guard_safe": size - unsafe, "guard_refusal_yes": rng.randint(0, size - unsafe),
                          "guard_refusal_no": 0,
                          "label_scores": {"scored": scored, "unscored": 0,
                                           **{label: {"sum": share * scored, "mean": share, "max": min(1.0, 2 * share)}
                                              for label, share in (("safe", 0.7), ("unsafe", unsafe / size),
                                                                   ("controversial", 0.05))}}}}
            groups[gid]["guard"]["guard_refusal_no"] = size - groups[gid]["guard"]["guard_refusal_yes"]
        return validate_view({"kind": VIEW_KIND, "split": split, "menu": ["a0", *ids], "groups": groups})

    def relevance(self) -> dict:
        rng = random.Random(derive_seed("world-relevance", self.seed))
        parts = {}
        for split in sorted(self.groups):
            parts[split] = {}
            for gid, (size, (d_f, _, _)) in sorted(self.groups[split].items()):
                top = _clamp(0.2 + max(0.0, -d_f) + rng.gauss(0, 0.02))
                values = {}
                for view in ("prompt", "pair"):
                    values.update({f"tfidf_{view}_mean": top / 2, f"tfidf_{view}_sum": top / 2 * size,
                                   f"tfidf_{view}_max": top})
                parts[split][gid] = {name: values[name] for name in RELEVANCE_FEATURES}
        return {"kind": TABLE_KIND, "definition_sha256": DEFINITION_SHA256,
                "fingerprint_sha256": sha256_bytes(f"synthetic-{self.seed}".encode()), "partitions": parts}

    def development_table(self, seeds, short: str, full: str) -> dict:
        """The development table built from synthetic dev evaluations through the real schema."""
        from types import SimpleNamespace

        view = self.view("dev")
        static, ties = view_features(SimpleNamespace(menu=view["menu"], groups=view["groups"]))
        relevance = self.relevance()["partitions"]["dev"]
        short_changes, full_changes, attribution, sources = {}, {}, {}, {}
        for seed in seeds:
            for fidelity, store in ((short, short_changes), (full, full_changes)):
                a0 = self._eval_obj("dev", "development", "a0", seed, fidelity, "dev")
                for gid in self.edits("dev"):
                    store[gid, seed] = paired_change(self._eval_obj("dev", "development", gid, seed, fidelity, "dev"), a0)
            attribution[seed] = self.attribution("dev", seed)
            sources[seed] = {"run": f"synthetic-attribution-{seed}", "complete_sha256": "0" * 64}
        return table_from_parts(split="dev", short=short, full=full, static=static, ties=ties, relevance=relevance,
                                seeds=list(seeds), short_changes=short_changes, full_changes=full_changes,
                                attribution=attribution, attribution_sources=sources,
                                inputs={"synthetic_world_seed": self.seed, "fixture": FIXTURE,
                                        "relevance_fingerprint_sha256": self.relevance()["fingerprint_sha256"],
                                        "catalogue_sha256": CATALOGUE_SHA256})

    def _eval_obj(self, split, role, arm, seed, checkpoint, bank) -> Evaluation:
        data = self.evaluation(split=split, role=role, arm=arm, seed=seed, checkpoint=checkpoint, bank=bank)
        return evaluation_from_artifact(arm, data, {"run": f"synthetic-{arm}-{seed}-{checkpoint}", "complete_sha256": "0" * 64})


def evaluation_from_artifact(arm: str, data: dict, source: dict) -> Evaluation:
    p = data["pairing"]
    coords = {"arm": arm, **{k: p[k] for k in ("seed", "split", "role", "checkpoint", "bank")}}
    return evaluation_from_counts(coords=coords, counts=data["counts"], query_nll=data["query_nll"], pairing=p,
                                  source=source, where=f"synthetic {arm}@{p['seed']}/{p['checkpoint']}")


def make_world(seed: int = 7, edits: int = 6) -> SyntheticWorld:
    """A small synthetic world: per split ``edits`` groups of sizes 8..64 with mixed effects."""
    rng = random.Random(derive_seed("make-world", seed))
    groups = {}
    for split in ("dev", "heldout"):
        groups[split] = {}
        for i in range(edits):
            gid = f"g-{derive_seed('world-id', seed, split, i) & ((1 << 64) - 1):016x}"
            groups[split][gid] = ((8, 16, 32, 64)[i % 4],
                                  (rng.uniform(-0.12, 0.04), rng.uniform(-0.01, 0.05), rng.uniform(-0.02, 0.04)))
    return SyntheticWorld(seed=seed, groups=groups)


SYNTHETIC_RECIPE = {"train": {"checkpoints": [{"name": "q", "epochs": [1, 4]}, {"name": "e1", "epochs": [1, 1]},
                                               {"name": "e3", "epochs": [3, 1]}]},
                    "attribution": {"checkpoints": ["q", "e1", "e3"]}}
SYNTHETIC_DATA_CONFIG = {"seed_namespaces": {"development": [1101, 2099], "selector": [2101, 8999],
                                             "reference": [9101, 9999]}}


def synthetic_pins(world: SyntheticWorld, table_sha256: str, record_sha256: str) -> dict:
    return {"engine_code_sha256": engine_code_identity()["sha256"],
            "policy_code_sha256": policy_code_identity()["sha256"],
            "manifest_sha256": sha256_bytes(f"synthetic manifest {world.seed}".encode()),
            "recipe_sha256": sha256_bytes(b"synthetic recipe"), "development_table_sha256": table_sha256,
            "development_record_sha256": record_sha256,
            "relevance_fingerprint_sha256": world.relevance()["fingerprint_sha256"]}


def prepare_synthetic(out: str | Path, world: SyntheticWorld, *, template: dict, spec: dict,
                      dev_seeds: tuple[int, ...] = (1101, 1102, 1103)) -> dict:
    """ENGINEERING: the synthetic development table and record, and a configuration derived from
    an ENGINEERING EXAMPLE template whose code- and record-dependent values (pins, the outcome
    definition pin, CV-selected lambdas, selected proxy, development group count) are copied from
    the code and the synthetic record. The status stays ENGINEERING EXAMPLE ONLY."""
    if template["status"] != EXAMPLE_STATUS:
        raise PolicyError("the synthetic exercise accepts only ENGINEERING EXAMPLE templates")
    if list(spec["x0"]) != list(template["features"]["x0"]):
        raise PolicyError("the fit spec's x0 must equal the template's features.x0")
    out = Path(out)
    short, full = template["fidelity"]["short"], template["fidelity"]["full"]
    table = world.development_table(dev_seeds, short, full)
    table_sha = write_once(out / "development-table.json", canonical_json(table))
    record = fit_record([(table, table_sha)], spec)
    record_sha = write_once(out / "development-record.json", canonical_json(record))
    entry = record["tables"][0]
    attribution = entry["selection"]["attribution"]
    config = copy.deepcopy(template)
    config["features"]["attribution"] = attribution
    config["predictor"]["development_groups"] = len(entry["groups"])
    config["predictor"]["selected_lambda"] = {
        "S-": {t: entry["fits"]["S-"]["targets"][t]["selected_lambda"] for t in TARGETS},
        "S+": {t: entry["fits"][f"S+/{attribution}"]["targets"][t]["selected_lambda"] for t in TARGETS}}
    pins = synthetic_pins(world, table_sha, record_sha)
    config["pins"] = dict(pins)
    config["outcome_definition"] = dict(OUTCOME_PIN)
    write_once(out / "config.json", canonical_json(config))
    return {"config": config, "record": record, "record_sha256": record_sha, "table_sha256": table_sha,
            "pins": pins, "recipe": SYNTHETIC_RECIPE, "data_config": SYNTHETIC_DATA_CONFIG}


class FakeBackend:
    """ENGINEERING FIXTURE backend over a SyntheticWorld with a fake clock (see module doc)."""

    engineering_fixture = True

    def __init__(self, world: SyntheticWorld) -> None:
        self.world = world
        self.now = 0.0
        self.executed: list[tuple[str, int]] = []
        self._setup_charged = False

    def clock(self) -> float:
        return self.now

    def sync(self) -> None:
        return None

    def execute(self, spec: dict, attempt_dir: Path, sources: Mapping[str, object]) -> dict:
        check_lock(spec, sources)
        attempt = int(Path(attempt_dir).name.rsplit("-", 1)[1])
        key = (spec["op_id"], attempt)
        if key in self.world.refusals:
            raise RequestRefused(f"ENGINEERING FIXTURE: scripted validation refusal of {spec['op_id']}")
        self.executed.append(key)
        setup = {}
        if not self._setup_charged and spec["kind"] not in ("export_view", "relevance", "score_groups"):
            setup, self._setup_charged = {"load_policy": self.world.session_setup_seconds}, True
        seconds = self.world.durations[spec["kind"]] * self.world.overrun.get(spec["op_id"], 1.0)
        if key in self.world.interrupts:
            self.now += seconds / 2
            raise KeyboardInterrupt(f"ENGINEERING FIXTURE: scripted interruption of {spec['op_id']}")
        self.now += seconds + sum(setup.values())
        if key in self.world.raises:
            raise OSError(f"ENGINEERING FIXTURE: {self.world.raises[key]}")
        if key in self.world.failures or (spec["kind"] == "final" and spec["arm"] in self.world.final_failures):
            write_once(Path(attempt_dir) / "failed.json", canonical_json({"op_id": spec["op_id"], "fixture": FIXTURE}))
            return {"status": "failed", "artifact": str(Path(attempt_dir) / "failed.json"), "artifact_sha256": None,
                    "error": "ENGINEERING FIXTURE: scripted technical failure", "engine_setup_seconds": setup}
        payload = {"op_id": spec["op_id"], "fixture": FIXTURE, "sources": {k: v for k, v in sorted(sources.items())
                                                                          if k != "lock"}}
        kind = spec["kind"]
        if kind in ("screen", "full_from_short", "full_from_init", "final"):
            payload["evaluation"] = self.world.evaluation(split=spec["split"], role=spec["role"], arm=spec["arm"],
                                                          seed=spec["seed"], checkpoint=spec["target"], bank=spec["bank"])
        elif kind == "attribution":
            payload["scores"] = self.world.attribution(spec["split"], spec["seed"])
        elif kind == "export_view":
            data = canonical_json(self.world.view(spec["split"]))
            digest = write_once(Path(attempt_dir) / "view.json", data)
            return {"status": "complete", "artifact": str(Path(attempt_dir) / "view.json"), "artifact_sha256": digest,
                    "error": None, "engine_setup_seconds": setup}
        elif kind == "relevance":
            data = canonical_json(self.world.relevance())
            digest = write_once(Path(attempt_dir) / "relevance.json", data)
            return {"status": "complete", "artifact": str(Path(attempt_dir) / "relevance.json"),
                    "artifact_sha256": digest, "error": None, "engine_setup_seconds": setup}
        data = canonical_json(payload)
        digest = write_once(Path(attempt_dir) / "artifact.json", data)
        return {"status": "complete", "artifact": str(Path(attempt_dir) / "artifact.json"), "artifact_sha256": digest,
                "error": None, "engine_setup_seconds": setup}

    def _payload(self, receipt: dict, spec: dict) -> dict:
        payload = read_canonical(receipt["artifact"], receipt["artifact_sha256"])
        if payload.get("op_id") != spec["op_id"]:
            raise VerificationError(f"{receipt['artifact']} is not the operation {spec['op_id']}")
        return payload

    def verify(self, receipt: dict, spec: dict) -> None:
        if spec["kind"] in ("export_view", "relevance"):
            read_canonical(receipt["artifact"], receipt["artifact_sha256"])
        else:
            self._payload(receipt, spec)

    def evaluation(self, receipt: dict, spec: dict) -> Evaluation:
        data = self._payload(receipt, spec)["evaluation"]
        return evaluation_from_artifact(spec["arm"], data, {"run": receipt["artifact"],
                                                            "complete_sha256": receipt["artifact_sha256"]})

    def attribution_scores(self, receipt: dict, spec: dict, a0_states: Mapping[str, str]) -> dict:
        payload = self._payload(receipt, spec)
        if payload["sources"].get("a0_states") != dict(a0_states):
            raise VerificationError("attribution used other a0 states")
        return payload["scores"]

    def static_inputs(self, view_receipt: dict, relevance_receipt: dict, split: str):
        view = read_selector_view(view_receipt["artifact"], view_receipt["artifact_sha256"])
        if view.split != split:
            raise VerificationError("the synthetic view is of another split")
        relevance, pins = read_relevance(relevance_receipt["artifact"], relevance_receipt["artifact_sha256"], split)
        return view, relevance, pins
