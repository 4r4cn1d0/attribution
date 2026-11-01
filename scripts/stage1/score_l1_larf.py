"""REQ-10: L1, LARF-style (RS B2; SPEC sections 2.4-2.6; addendum L3, L4; UW-11 (b)-(d); outside the engine identity;
the scan runs on a stage-1 pod, the score on the Mac; CPU-tested; CUDA paths UNTESTED; model-agnostic).

    python scripts/stage1/score_l1_larf.py scan --prepared P --recipe REC --anchors BANK --out DIR
    python scripts/stage1/score_l1_larf.py score --prepared P --scan PATH:SHA256 --rows PATH:SHA256
        --summary PATH:SHA256 --out DIR

**Scan.** Scan prompts: BANK's 64 harmful anchor prompts and 64 Dolly training prompts, the sealed sample of key
l1.scan over all training row ids (sorted). REC's policy runs UNTUNED (disable_adapter, no gradients); each
configuration answers all 128 prompts greedily with ``max_new_tokens`` 32 and REC's stop tokens, in one call with REC's
batch size; a refusal = lexicon class REFUSAL-OPENING (REQ-1). Scaling (UW-11 (d)): forward hooks multiply the outputs of
block l's modules named in the settings for the model's architecture (OLMo-2: post_attention_layernorm and
post_feedforward_layernorm) by (1 + alpha) and (1 - alpha), alpha in the settings' list (0.1, 0.2); every block is run
and logged; blocks from ``first_block`` to the last are eligible. c+ and c- are the refusal counts over the 128 prompts;
Delta_l(alpha) = c+ - c-; k_l = max over alpha of Delta_l(alpha) / alpha; l_s = argmax k_l over the eligible blocks, ties
to the larger Delta_l(first alpha), then the lower index; if max k_l <= 0, l_s = the last block, recorded as no signal.
The hooks are removed after each configuration (the model is unchanged afterwards).

**Score.** From REQ-3's rows file (named by SHA-256, with its summary): for every training row, score = cos_harmful -
cos_safe at hidden-state index block_output_index(l_s, n) = l_s + 1 (index n, the final-norm output, when l_s = n - 1;
recorded) and read (a) (L3; the end-of-turn position), float64. Written as T1's scorer output (scorer "l1", high = remove);
write_score_edit.py's scorer path selects the top 600 (REQ-14, ties by that writer's own registry key).

Outputs: ``l1_scan.json`` (text-free: per block, alpha and sign the refusal counts, by subset; k_l; l_s; the index;
each configuration's answers' SHA-256; costs; provenance) and ``l1_scores.json`` (the scorer output).
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import lexicon_pin  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "score_l1_larf.json"
SETTINGS_SHA256 = "0d875213831d30456ffc02254cca839d78ae48da8d7ba35d037561b9d59a75cd"
SETTINGS_NAME = "score_l1_larf"
SCAN_FILE, SCORES_FILE = "l1_scan.json", "l1_scores.json"


# ----- hooks --------------------------------------------------------------------------------------------------------


def scale_modules(model, block: int, settings: dict) -> list:
    """The modules of block ``block`` whose outputs the scan scales, by the model's architecture."""
    from scripts.stage1.representation_pass import base_model

    base = base_model(model)
    names = settings["scan"]["modules"].get(base.config.model_type)
    if names is None:
        raise s1.Refusal(f"the settings name no scaled modules for model type {base.config.model_type!r}")
    layer = base.get_decoder().layers[block]
    out = []
    for name in names:
        if not hasattr(layer, name):
            raise s1.Refusal(f"block {block} has no module {name}")
        out.append(getattr(layer, name))
    return out


class Scaled:
    """A context: forward hooks that multiply the outputs of the given modules by ``factor`` (the first element of a
    tuple output), removed on exit."""

    def __init__(self, modules: list, factor: float):
        self.modules, self.factor, self.handles = modules, factor, []

    def hook(self, module, inputs, output):
        if isinstance(output, tuple):
            return (output[0] * self.factor,) + tuple(output[1:])
        return output * self.factor

    def __enter__(self):
        self.handles = [m.register_forward_hook(self.hook) for m in self.modules]
        return self

    def __exit__(self, *exc):
        for h in self.handles:
            h.remove()
        self.handles = []
        return False


# ----- the layer scan -----------------------------------------------------------------------------------------------


def choose_layer(counts: dict, n_layers: int, settings: dict) -> dict:
    """l_s from the per-block counts {block: {alpha: (c_plus, c_minus)}} (module doc)."""
    alphas = settings["scan"]["alphas"]
    first = settings["scan"]["first_block"]
    eligible = [b for b in range(n_layers) if b >= first]
    if not eligible:
        raise s1.Refusal(f"no block is eligible: the model has {n_layers} blocks, the first eligible is {first}")
    delta = {b: {a: counts[b][a][0] - counts[b][a][1] for a in alphas} for b in range(n_layers)}
    k = {b: max(delta[b][a] / a for a in alphas) for b in range(n_layers)}
    best = max(k[b] for b in eligible)
    if best <= 0:
        return {"l_s": n_layers - 1, "no_signal": True, "delta": delta, "k": k}
    tied = [b for b in eligible if k[b] == best]
    top = max(delta[b][alphas[0]] for b in tied)
    tied = [b for b in tied if delta[b][alphas[0]] == top]
    return {"l_s": min(tied), "no_signal": False, "delta": delta, "k": k}


def scan_prompts(prepared_root: Path, anchors_path: Path, settings: dict) -> tuple[list[dict], dict]:
    """BANK's harmful prompts and the sealed sample of Dolly training prompts (text in memory only)."""
    from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: F401
    from experiments.safety_selection.prepare import load_prepared

    pins = settings["pins"]
    if sha256_file(anchors_path) != pins["anchor_bank_sha256"]:
        raise s1.Refusal(f"the anchor bank hashes to {sha256_file(anchors_path)}, the settings pin {pins['anchor_bank_sha256']}")
    bank = s1.strict_json(Path(anchors_path).read_bytes())
    harmful = bank.get("harmful") if isinstance(bank, dict) else None
    if not isinstance(harmful, list) or len(harmful) != settings["scan"]["harmful_anchors"]:
        raise s1.Refusal(f"the anchor bank does not hold {settings['scan']['harmful_anchors']} harmful anchors")
    prepared = load_prepared(prepared_root, pins["prepared_manifest_sha256"])
    rows = s1.sealed_sample(sorted(prepared.train_rows), settings["scan"]["dolly"], "l1.scan")
    prompts = [{"id": a["anchor_id"], "subset": "harmful", "prompt": a["prompt"]} for a in harmful] + \
              [{"id": r, "subset": "dolly", "prompt": prepared.train_rows[r]["prompt"]} for r in rows]
    return prompts, {"anchor_ids": [a["anchor_id"] for a in harmful], "dolly_row_ids": rows}


def run_scan(*, prepared_root: Path, recipe_path: Path, anchors_path: Path, loaders, settings: dict,
             settings_sha256: str, generate=None) -> dict[str, bytes]:
    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        return _scan(prepared_root, recipe_path, anchors_path, loaders, settings, settings_sha256, generate, Path(scratch))


def _scan(prepared_root, recipe_path, anchors_path, loaders, settings, settings_sha256, generate, scratch):
    import torch

    from experiments.safety_selection import engine as en
    from experiments.safety_selection import runner
    from experiments.safety_selection.config import config_sha256, load_recipe
    from experiments.safety_selection.ledger import RunLedger
    from experiments.safety_selection.textproc import encode_generation_prompt
    from scripts.stage1.representation_pass import check_transformers, layout

    s1.check_settings(settings, SETTINGS_NAME)
    check_transformers(settings)
    recipe = load_recipe(recipe_path)
    if config_sha256(recipe) != settings["pins"]["rec_recipe_sha256"]:
        raise s1.Refusal(f"REC hashes to {config_sha256(recipe)}, the settings pin {settings['pins']['rec_recipe_sha256']}")
    prompts, ids_record = scan_prompts(prepared_root, anchors_path, settings)
    lexicon = lexicon_pin.load()
    session = runner.Session(recipe, loaders)
    ledger = RunLedger(scratch, sync=session.sync, memory=session.memory)
    policy = session.policy(ledger, scratch)
    codec, model, device = policy.codec, policy.model, policy.device
    lay = layout(model)
    n = lay["n_layers"]
    ids = []
    for p in prompts:
        try:
            ids.append(encode_generation_prompt(codec, p["prompt"], recipe["model"]["max_prompt_tokens"]))
        except ValueError as exc:
            raise s1.Refusal(f"scan prompt {p['id']} is not a generation prompt ({type(exc).__name__})") from None
    spec = settings["scan"]

    def answers():
        if generate is not None:
            return generate(model, ids)
        with torch.no_grad(), model.disable_adapter():
            gens = en.greedy_generate(model, ids, max_new_tokens=spec["max_new_tokens"], stop_ids=codec.stop_ids,
                                      pad_id=codec.pad_id, device=device, batch_size=recipe["generation"]["batch_size"])
        return [codec.decode(g.output_ids) for g in gens]

    def count(texts):
        flags = [lexicon.classify(t) == "REFUSAL-OPENING" for t in texts]
        return {"all": sum(flags), **{sub: sum(f for f, p in zip(flags, prompts) if p["subset"] == sub)
                                      for sub in ("harmful", "dolly")}}, sha256_bytes(canonical_json(texts))

    session.sync()
    started = time.monotonic()
    base_texts = answers()
    baseline, baseline_sha = count(base_texts)
    configs, counts = [], {}
    for block in range(n):
        modules = scale_modules(model, block, settings)
        counts[block] = {}
        for alpha in spec["alphas"]:
            pair = []
            for sign in (1, -1):
                with Scaled(modules, 1 + sign * alpha):
                    c, digest = count(answers())
                pair.append(c["all"])
                configs.append({"block": block, "alpha": alpha, "sign": sign, "refusals": c, "answers_sha256": digest})
            counts[block][alpha] = tuple(pair)
    session.sync()
    seconds = time.monotonic() - started
    chosen = choose_layer(counts, n, settings)
    from scripts.stage1.representation_pass import block_output_index

    index = block_output_index(chosen["l_s"], n)
    record = {"kind": "stage1 l1 layer scan", "version": 1, "requirement": settings["requirement"], "layout": lay,
              "prompts": {"harmful": spec["harmful_anchors"], "dolly": spec["dolly"], **ids_record},
              "baseline": {"refusals": baseline, "answers_sha256": baseline_sha}, "configurations": configs,
              "delta": {str(b): {str(a): v for a, v in d.items()} for b, d in chosen["delta"].items()},
              "k": {str(b): v for b, v in chosen["k"].items()}, "l_s": chosen["l_s"], "no_signal": chosen["no_signal"],
              "index": index, "index_is_final_norm": index == n, "rule": spec["rule"],
              "costs": {"device": device, "scan_seconds": seconds, "generations": 1 + len(configs)},
              "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                          {"rec_recipe": settings["pins"]["rec_recipe_sha256"],
                                           "anchor_bank": settings["pins"]["anchor_bank_sha256"],
                                           "prepared_manifest": settings["pins"]["prepared_manifest_sha256"]},
                                          settings["label_entries"])}
    data = canonical_json(record)
    if s1._text_hits(data, [p["prompt"] for p in prompts] + list(base_texts)):
        raise s1.Refusal("the scan record would hold text")
    return {SCAN_FILE: data}


# ----- the score ------------------------------------------------------------------------------------------------------


def read_pinned_json(path: Path, digest: str, what: str):
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {digest}")
    return data


def scores_from(rows_bytes: bytes, rows_sha256: str, summary_doc: dict, scan_doc: dict, settings: dict) -> tuple[dict, int]:
    """L1's score of every dev row of REQ-3's rows file, and the hidden-state index read (module doc)."""
    from scripts.stage1 import representation_pass as rp

    if scan_doc.get("kind") != "stage1 l1 layer scan":
        raise s1.Refusal("the scan file is not an L1 layer scan")
    if summary_doc.get("kind") != "stage1 representation pass" or summary_doc["rows"]["sha256"] != rows_sha256:
        raise s1.Refusal("the rows file is not the one REQ-3's summary names")
    if summary_doc["provenance"]["settings_sha256"] != settings["pins"]["representation_pass_settings_sha256"]:
        raise s1.Refusal("REQ-3's summary was not made with the pinned REQ-3 settings")
    n = summary_doc["layout"]["n_layers"]
    if scan_doc["layout"]["n_layers"] != n:
        raise s1.Refusal("the scan and REQ-3 read models with different layer counts")
    index = rp.block_output_index(scan_doc["l_s"], n)
    if index != scan_doc["index"]:
        raise s1.Refusal("the scan's index is not block_output_index(l_s, n)")
    read = rp.READS.index(settings["score"]["read"])
    scores = {}
    for line in s1.iter_jsonl_bytes(rows_bytes, "REQ-3's rows file"):
        if line.get("source") != "dev":
            continue
        value = float(line["cos_harmful"][index][read]) - float(line["cos_safe"][index][read])
        if not math.isfinite(value):
            raise s1.Refusal(f"row {line['id']}: a non-finite L1 score")
        scores[line["id"]] = value
    return scores, index


def build_score(*, prepared_root: Path, scan: tuple[Path, str], rows: tuple[Path, str], summary: tuple[Path, str],
                settings: dict, settings_sha256: str) -> dict[str, bytes]:
    s1.check_settings(settings, SETTINGS_NAME)
    view = s1.PreparedView(prepared_root, settings["pins"]["prepared_manifest_sha256"])
    scan_doc = s1.strict_json(read_pinned_json(*scan, "the scan file"))
    summary_doc = s1.strict_json(read_pinned_json(*summary, "REQ-3's summary"))
    rows_bytes = read_pinned_json(*rows, "REQ-3's rows file")
    scores, index = scores_from(rows_bytes, rows[1], summary_doc, scan_doc, settings)
    s1.check_scores(scores, view.tokens)
    doc = {"kind": settings["scorer_output"]["kind"], "version": settings["scorer_output"]["version"], "scorer": "l1",
           "manifest_sha256": view.manifest_sha256, "orientation": settings["scorer_output"]["orientation"],
           "scores": dict(sorted(scores.items())),
           "costs": {"scan": scan_doc["costs"], "representation_pass": summary_doc["costs"], "score_seconds": 0.0},
           "provenance": {**s1.provenance(Path(__file__).resolve(), settings_sha256,
                                          {"scan": scan[1], "rows": rows[1], "summary": summary[1],
                                           "prepared_manifest": view.manifest_sha256}, settings["label_entries"]),
                          "index": index, "read": settings["score"]["read"], "l_s": scan_doc["l_s"],
                          "no_signal": scan_doc["no_signal"]}}
    return {SCORES_FILE: canonical_json(doc)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p_scan = sub.add_parser("scan")
    for flag in ("--prepared", "--recipe", "--anchors", "--out"):
        p_scan.add_argument(flag, type=Path, required=True)
    p_score = sub.add_parser("score")
    p_score.add_argument("--prepared", type=Path, required=True)
    for flag in ("--scan", "--rows", "--summary"):
        p_score.add_argument(flag, required=True, help="PATH:SHA256")
    p_score.add_argument("--out", type=Path, required=True)
    for p in (p_scan, p_score):
        p.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        if args.command == "scan":
            from experiments.safety_selection.loaders import real_loaders

            files = run_scan(prepared_root=args.prepared, recipe_path=args.recipe, anchors_path=args.anchors,
                             loaders=real_loaders(), settings=settings, settings_sha256=digest)
        else:
            def pair(spec):
                path, _, sha = spec.rpartition(":")
                if not path or not s1.HEX64.match(sha):
                    raise s1.Refusal("--scan, --rows and --summary are PATH:SHA256")
                return Path(path), sha
            files = build_score(prepared_root=args.prepared, scan=pair(args.scan), rows=pair(args.rows),
                                summary=pair(args.summary), settings=settings, settings_sha256=digest)
        written = s1.write_new_files(args.out.resolve(), files)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
