"""B14, part 1: the overlap control's similarity pass (RS B14; PLAN-S:172, :214; stage-1 pre-registration DRAFT
revision 2, section 9.4; outside the engine identity; CPU-tested with a tiny model; it runs on a pod).

    python -B scripts/stage1_s1/overlap_similarity.py --prepared P --recipe REC --out DIR \\
        --add-set S1 FILE SHA256 [--add-set S3 FILE SHA256] [--add-set S4 FILE SHA256]

**What the sources fix.** PLAN-S:172: "report each eval prompt's highest similarity to the add set (untuned-model
embeddings, on the pod); the add effect must hold on the lower-similarity half". No source fixes the layer, the
position, the text of an added row or the ties (repo-requirements.md:267 lists them as open; the mock review A,
question 12, asks the same). This script's reading is pinned in ``settings/overlap_similarity.json``:

- **Model.** The untuned policy theta0: the recipe's policy with its adapter disabled
  (``policy.model.disable_adapter()``), eval mode, no gradients. The engine's own loaders and codec load it.
- **Text.** A prompt only. An evaluation prompt is a dev-bank item of the settings' kinds (the 200 harm prompts); it
  is encoded with ``encode_generation_prompt`` and must match the prepared token audit (``token_sha256``). An added
  row's prompt is encoded the same way, and the row must also pass ``encode_train`` (as training encodes it; both
  take the prompt part from the same ``codec.prompt_ids``). The response is not embedded: in a causal model the
  states at the prompt positions do not depend on the response, so the vector is also the added row's training
  state at its last prompt position (a test checks this).
- **Embedding.** v = the hidden state at index L (settings; 16 = model.norm(the output of the last block), the
  convention of addendum L4) at the last prompt position, len - 1 (the last token of the assistant header; REQ-3's
  read (d)), from one unbatched forward, cast to float64 on the CPU. The model must have the settings' block count.
- **Similarity.** s(e, a) = (v_e . v_a) / (||v_e|| ||v_a||) in float64, no rounding. A zero norm or a non-finite
  value refuses.
- **Highest similarity.** S(e; A) = the largest s(e, a) over the rows a of add set A. The nearest row is a row that
  attains it; rows with an exactly equal value go to the smallest row id (report only; S does not depend on it).

**Inputs.** The prepared set P (its manifest pinned; only ``banks/dev.jsonl`` is read, after its manifest hash
verifies; never the selector or hidden bank); the recipe (pinned by ``config_sha256``); one edit file per add set
(``--add-set NAME FILE SHA256``; NAME in the settings' list; the bytes must hash to SHA256; the engine's own
``parse_edit`` reads it; it must be a pure ``add`` edit of the settings' row count, for P's manifest). The checks of
the settings, the transformers version, the recipe, the bank and the edit files, and the check that DIR does not
exist, run before the model loads. The checks that need the loaded policy run after the load: the block count, the
token audit of each evaluation prompt and the codec checks of each added row (``encode_train`` and
``encode_generation_prompt``). Such a refusal leaves DIR with the engine's ledger and no ``similarity.json``, so the
next try needs a new ``--out``.

**Output** (DIR must not exist): ``similarity.json`` (canonical JSON: prompt ids, row ids, numbers and hashes; no
prompt or response text; the bytes are scanned for every text before they are written) and the engine's
``ledger.jsonl``. Costs: GPU-seconds of setup and of the forward passes, tokens, peak memory (CUDA only; the setup
peak is the larger of the script's own read and the CUDA peaks that the ledger's stages recorded, because the
engine's memory probe resets the CUDA peak at the end of each stage, the model load included).
Prints counts and hashes only. Exit 0: written; exit 2: refused. The CUDA path and the real OLMo-2 template are
UNTESTED here.
"""

from __future__ import annotations

import argparse
import math
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, ids_sha256, sha256_bytes, sha256_file, write_atomic  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1.limits import limits_common as lc  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "overlap_similarity.json"
SETTINGS_SHA256 = "27db4c3faafc41c4278ff6ca7d1ded0a0fb1a07ae484c4bbf65702f5545ac754"
SETTINGS_NAME = "overlap_similarity"
RECORD_KIND = "stage1 overlap similarity"
OUTPUT = "similarity.json"
READ = "prompt_last"
SET_NAME = re.compile(r"^[A-Z][A-Za-z0-9]{0,15}$")
COSINE_SLACK = 1e-9                      # |cos| may exceed 1 by rounding only


# ----- settings --------------------------------------------------------------------------------------------------


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def check_content(doc: Mapping[str, Any]) -> None:
    """The settings' own content (s1common.check_settings checks kind, name, registry entries and engine X)."""
    for key in ("transformers_version", "requirement"):
        if not isinstance(doc.get(key), str) or not doc[key]:
            raise s1.Refusal(f"settings: {key} is missing")
    lc.hex64(doc.get("prepared_manifest_sha256"), "settings: prepared_manifest_sha256")
    lc.hex64(doc.get("recipe_sha256"), "settings: recipe_sha256")
    if doc.get("label_entries") != {}:
        raise s1.Refusal("settings: this script draws nothing, so label_entries must be empty")
    ev = doc.get("eval") or {}
    if ev.get("bank") != "dev":
        raise s1.Refusal("settings: the evaluation prompts come from the dev bank only")
    kinds = ev.get("kinds")
    if not (isinstance(kinds, list) and kinds and all(isinstance(k, str) and k for k in kinds)
            and len(set(kinds)) == len(kinds)):
        raise s1.Refusal("settings: eval.kinds is not a list of distinct bank kinds")
    if not _positive_int(ev.get("prompts")):
        raise s1.Refusal("settings: eval.prompts is not a positive count")
    sets = doc.get("add_sets") or {}
    names = sets.get("names")
    if not (isinstance(names, list) and names and all(isinstance(n, str) and SET_NAME.match(n) for n in names)
            and len(set(names)) == len(names)):
        raise s1.Refusal("settings: add_sets.names is not a list of distinct short names")
    if not _positive_int(sets.get("rows_each")) or sets.get("edit_kind") != "add":
        raise s1.Refusal("settings: an add set is a pure add edit of a positive row count")
    emb = doc.get("embedding") or {}
    if emb.get("read") != READ:
        raise s1.Refusal(f"settings: the read must be {READ}")
    n_layers, index = emb.get("n_layers"), emb.get("hidden_state_index")
    if not _positive_int(n_layers) or isinstance(index, bool) or not isinstance(index, int) or not 0 <= index <= n_layers:
        raise s1.Refusal("settings: the hidden-state index is not in 0..n_layers")
    sim = doc.get("similarity") or {}
    if sim.get("measure") != "cosine" or sim.get("aggregate") != "max":
        raise s1.Refusal("settings: the similarity is the cosine and the aggregate is the max")


def check_transformers(settings: Mapping[str, Any]) -> str:
    import transformers

    version = transformers.__version__
    if version != settings["transformers_version"]:
        raise s1.Refusal(f"transformers is {version}, the settings pin {settings['transformers_version']}")
    return version


# ----- inputs (all checked before the model loads) ---------------------------------------------------------------


def eval_prompts(prepared_dir: Path, settings: Mapping[str, Any]) -> tuple[list[dict], str, str, str]:
    """(items, manifest SHA-256, bank file name, bank file SHA-256): the dev bank's items of the settings' kinds,
    each reduced to prompt_id, kind, prompt and token_sha256. Only the manifest and banks/dev.jsonl are read."""
    from experiments.safety_selection.prepare import BANK_FILES, read_manifest, read_verified
    from experiments.safety_selection.sources import DataError

    try:
        manifest, manifest_sha = read_manifest(prepared_dir, settings["prepared_manifest_sha256"])
    except (DataError, OSError):
        raise s1.Refusal("the prepared manifest is missing or is not the pinned one") from None
    name = BANK_FILES["dev"]
    if name not in (manifest.get("files") or {}):
        raise s1.Refusal(f"the prepared manifest lists no {name}")
    try:
        data = read_verified(prepared_dir, manifest, name)
    except (DataError, OSError):
        raise s1.Refusal(f"{name} is missing or differs from the manifest hash") from None
    kinds = set(settings["eval"]["kinds"])
    items, seen = [], set()
    for record in s1.iter_jsonl_bytes(data, name):
        if record.get("kind") in kinds:
            item = {k: record.get(k) for k in ("prompt_id", "kind", "prompt", "token_sha256")}
            if not isinstance(item["prompt_id"], str) or item["prompt_id"] in seen:
                raise s1.Refusal("the evaluation prompt ids are not distinct strings")
            if not isinstance(item["prompt"], str) or not isinstance(item["token_sha256"], str):
                raise s1.Refusal(f"evaluation prompt {item['prompt_id']} has no prompt or no token audit")
            seen.add(item["prompt_id"])
            items.append(item)
        record.clear()
    if len(items) != settings["eval"]["prompts"]:
        raise s1.Refusal(f"the dev bank holds {len(items)} prompts of kinds {sorted(kinds)}, "
                         f"not {settings['eval']['prompts']}")
    return sorted(items, key=lambda i: i["prompt_id"]), manifest_sha, name, sha256_bytes(data)


@dataclass(frozen=True)
class _ManifestOnly:
    """What parse_edit reads of a prepared set for a pure add edit (no training row is touched by one)."""
    manifest_sha256: str
    train_rows: dict = field(default_factory=dict)
    groups: dict = field(default_factory=lambda: {"heldout": {}})


def add_sets(given: Sequence[tuple[str, Path, str]], settings: Mapping[str, Any], manifest_sha256: str) -> dict:
    """name -> {edit_sha256, arm, rows: [(row id, prompt, response)]}, from the named edit files."""
    from experiments.safety_selection.edits import EditError, parse_edit

    allowed, rows_each = settings["add_sets"]["names"], settings["add_sets"]["rows_each"]
    out: dict[str, dict] = {}
    digests: set[str] = set()
    if not given:
        raise s1.Refusal("no add set is named")
    for name, path, digest in given:
        if name not in allowed or name in out:
            raise s1.Refusal(f"add set {name!r} is not one of {allowed}, or is named twice")
        digest = lc.hex64(digest, f"the SHA-256 of add set {name}")
        if digest in digests:
            raise s1.Refusal(f"add set {name}: the same edit file is named twice")
        try:
            data = Path(path).read_bytes()
        except OSError:
            raise s1.Refusal(f"add set {name}: the edit file cannot be read") from None
        if sha256_bytes(data) != digest:
            raise s1.Refusal(f"add set {name}: the edit file hashes to {sha256_bytes(data)}, not {digest}")
        try:
            edit = parse_edit(data, _ManifestOnly(manifest_sha256))
        except EditError as exc:
            raise s1.Refusal(f"add set {name}: the engine refuses the edit file ({type(exc).__name__})") from None
        if edit.document["edit_kind"] != settings["add_sets"]["edit_kind"] or edit.removed or edit.rewrite:
            raise s1.Refusal(f"add set {name}: the edit is not a pure add edit")
        if len(edit.added) != rows_each:
            raise s1.Refusal(f"add set {name}: the edit adds {len(edit.added)} rows, not {rows_each}")
        digests.add(digest)
        out[name] = {"edit_sha256": digest, "arm": edit.arm, "rows": list(edit.added)}
    return dict(sorted(out.items()))


# ----- encoding, the model and the vectors --------------------------------------------------------------------------


def encode_eval(codec: Any, item: Mapping[str, Any], max_prompt_tokens: int) -> list[int]:
    """The generation-prompt ids of one evaluation prompt, which must match the prepared token audit."""
    from experiments.safety_selection.textproc import ControlTokenError, TooLong, encode_generation_prompt

    try:
        ids = encode_generation_prompt(codec, item["prompt"], max_prompt_tokens)
    except (ControlTokenError, TooLong) as exc:
        raise s1.Refusal(f"evaluation prompt {item['prompt_id']} is refused by the codec ({type(exc).__name__})") from None
    if ids_sha256(ids) != item["token_sha256"]:
        raise s1.Refusal(f"evaluation prompt {item['prompt_id']} encodes differently from the prepared token audit")
    return ids


def encode_added(codec: Any, row_id: str, prompt: str, response: str, recipe: Mapping[str, Any]) -> list[int]:
    """The generation-prompt ids of one added row's prompt (encode_generation_prompt under the recipe's prompt limit).
    The row must also pass encode_train, as training will encode it. Both encodings take the prompt part from the
    same codec.prompt_ids, so the vector is also the row's training state at its last prompt position."""
    from experiments.safety_selection.textproc import (ControlTokenError, NoTargets, TooLong, encode_generation_prompt,
                                                       encode_train)

    model = recipe["model"]
    try:
        encode_train(codec, row_id, prompt, response, model["max_train_tokens"])
        return encode_generation_prompt(codec, prompt, model["max_prompt_tokens"])
    except (ControlTokenError, NoTargets, TooLong) as exc:
        raise s1.Refusal(f"added row {row_id} is refused by the codec ({type(exc).__name__})") from None


def layout(model: Any) -> dict:
    """Model type, block count and hidden size, read from the loaded model (never assumed)."""
    base = model.get_base_model() if hasattr(model, "get_base_model") else model
    config = base.config
    return {"model_type": str(config.model_type), "n_layers": int(config.num_hidden_layers),
            "hidden_size": int(config.hidden_size)}


def prompt_vector(model: Any, ids: Sequence[int], index: int, n_layers: int, device: str) -> Any:
    """One unbatched forward of a prompt: the hidden state at ``index`` and the last position, float64 on the CPU."""
    import torch

    tensor = torch.tensor([list(ids)], device=device)
    hidden = model(input_ids=tensor, output_hidden_states=True).hidden_states
    if len(hidden) != n_layers + 1:
        raise s1.Refusal(f"the model returned {len(hidden)} hidden states, not n_layers + 1 = {n_layers + 1}")
    vector = hidden[index][0, len(ids) - 1].to(torch.float64).cpu()
    if not bool(torch.isfinite(vector).all()):
        raise s1.Refusal("a prompt vector is not finite")
    return vector


def cosine_table(eval_vectors: Sequence[Any], add_vectors: Sequence[Any]) -> list[list[float]]:
    """cos[i][k] = (e_i . a_k) / (||e_i|| ||a_k||) in float64; a zero norm or a non-finite value refuses."""
    import torch

    e, a = torch.stack(list(eval_vectors)), torch.stack(list(add_vectors))
    e_norm, a_norm = torch.linalg.vector_norm(e, dim=1), torch.linalg.vector_norm(a, dim=1)
    if bool((e_norm == 0).any()) or bool((a_norm == 0).any()):
        raise s1.Refusal("a prompt vector has norm 0, so its cosine is undefined")
    table = (e @ a.T) / torch.outer(e_norm, a_norm)
    if not bool(torch.isfinite(table).all()) or float(table.abs().max()) > 1 + COSINE_SLACK:
        raise s1.Refusal("a cosine is not finite or lies outside [-1, 1]")
    return table.tolist()


def highest(table: Sequence[Sequence[float]], prompt_ids: Sequence[str], row_ids: Sequence[str]) -> dict:
    """prompt id -> {s_max, nearest}: the largest cosine over the add set's rows, and the smallest row id that
    attains it (exact float equality)."""
    out = {}
    for pid, row in zip(prompt_ids, table, strict=True):
        best = max(row)
        nearest = min(rid for rid, value in zip(row_ids, row, strict=True) if value == best)
        out[pid] = {"s_max": float(best), "nearest": nearest}
    return out


def _summary(per_prompt: Mapping[str, Mapping[str, Any]], row_ids: Sequence[str]) -> dict:
    values = [v["s_max"] for v in per_prompt.values()]
    nearest = {rid: 0 for rid in row_ids}
    for v in per_prompt.values():
        nearest[v["nearest"]] += 1
    return {"min": min(values), "median": statistics.median(values), "max": max(values),
            "distinct_values": len(set(values)), "nearest_counts": nearest}


def _reset_peak(device: str) -> None:
    import torch

    if device == "cuda":                                       # untested on CUDA
        torch.cuda.reset_peak_memory_stats()


def _peak(device: str) -> int | None:
    import torch

    return int(torch.cuda.max_memory_allocated()) if device == "cuda" else None


def _setup_peak(peak: int | None, out: Path) -> int | None:
    """The setup phase's peak: the larger of the script's own ``peak`` and the CUDA peak that each ledger stage
    written so far recorded (the engine's memory probe resets the CUDA peak when a stage ends, so the script's own
    read misses the model load; the same rule as ``scripts/gate_c_representation.py``'s ``_setup_peak``). None when
    neither is a number (off CUDA, or no ledger stage yet). Untested on CUDA."""
    from experiments.safety_selection.common import read_jsonl
    from experiments.safety_selection.ledger import LEDGER

    path = Path(out) / LEDGER
    stages = [(r.get("memory") or {}).get("cuda_peak_allocated_bytes") for r in read_jsonl(path)] \
        if path.is_file() else []
    values = [v for v in (peak, *stages) if isinstance(v, int) and not isinstance(v, bool)]
    return max(values) if values else None


# ----- the pass ------------------------------------------------------------------------------------------------------


def run(prepared_dir: Path, recipe_path: Path, given: Sequence[tuple[str, Path, str]], out: Path, loaders: Any,
        settings: Mapping[str, Any], settings_sha256: str) -> tuple[dict, bytes]:
    """The checked pass; returns (record, its bytes) after writing DIR/similarity.json."""
    import torch

    from experiments.safety_selection import runner
    from experiments.safety_selection.config import ConfigError, config_sha256, load_recipe
    from experiments.safety_selection.ledger import RunLedger

    check_content(settings)
    version = check_transformers(settings)
    try:
        recipe = load_recipe(recipe_path)
    except (ConfigError, OSError, ValueError):
        raise s1.Refusal("the recipe cannot be read or is invalid") from None
    recipe_sha = config_sha256(recipe)
    if recipe_sha != settings["recipe_sha256"]:
        raise s1.Refusal(f"the recipe hashes to {recipe_sha}, the settings pin {settings['recipe_sha256']}")
    items, manifest_sha, bank_name, bank_sha = eval_prompts(Path(prepared_dir), settings)
    sets = add_sets(given, settings, manifest_sha)
    out = Path(out)
    if out.exists():
        raise s1.Refusal(f"{out} exists: a similarity pass writes one new folder")
    emb = settings["embedding"]
    index, n_layers = emb["hidden_state_index"], emb["n_layers"]

    started = time.monotonic()
    out.mkdir(parents=True)
    session = runner.Session(recipe, loaders)
    _reset_peak(session.device)
    ledger = RunLedger(out, sync=session.sync, memory=session.memory)
    policy = session.policy(ledger, out)
    codec, device, model = policy.codec, policy.device, policy.model
    shape = layout(model)
    if shape["n_layers"] != n_layers:
        raise s1.Refusal(f"the model has {shape['n_layers']} blocks, the settings pin {n_layers}")
    max_prompt = recipe["model"]["max_prompt_tokens"]
    eval_ids = [encode_eval(codec, item, max_prompt) for item in items]
    add_ids = {name: [encode_added(codec, rid, prompt, response, recipe) for rid, prompt, response in s["rows"]]
               for name, s in sets.items()}
    setup = {"seconds": time.monotonic() - started, "peak_memory_bytes": _setup_peak(_peak(device), out)}

    started = time.monotonic()
    _reset_peak(device)
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad(), model.disable_adapter():                      # theta0: the untuned model
            eval_vectors = [prompt_vector(model, ids, index, n_layers, device) for ids in eval_ids]
            add_vectors = {name: [prompt_vector(model, ids, index, n_layers, device) for ids in rows]
                           for name, rows in add_ids.items()}
    finally:
        model.train(was_training)
    sequences = eval_ids + [ids for rows in add_ids.values() for ids in rows]
    forward = {"seconds": time.monotonic() - started, "forwards": len(sequences),
               "tokens": sum(len(ids) for ids in sequences), "peak_memory_bytes": _peak(device)}

    prompt_ids = [item["prompt_id"] for item in items]
    block = {}
    for name, s in sets.items():
        row_ids = [rid for rid, _, _ in s["rows"]]
        per_prompt = highest(cosine_table(eval_vectors, add_vectors[name]), prompt_ids, row_ids)
        block[name] = {"edit_sha256": s["edit_sha256"], "arm": s["arm"], "rows": len(row_ids), "row_ids": row_ids,
                       "per_prompt": per_prompt, "summary": _summary(per_prompt, row_ids)}
    inputs = {"prepared/manifest.json": manifest_sha, f"prepared/{bank_name}": bank_sha, "recipe": recipe_sha,
              **{f"add/{name}": s["edit_sha256"] for name, s in sets.items()}}
    doc = {"kind": RECORD_KIND, "version": 1, "requirement": settings["requirement"],
           "definition": {"embedding": emb, "similarity": settings["similarity"]},
           "model": {"repo_id": recipe["model"]["repo_id"], "revision": recipe["model"]["revision"],
                     "untuned": "policy.model.disable_adapter()", **shape, "hidden_state_index": index,
                     "read": READ, "transformers": version},
           "eval": {"bank": settings["eval"]["bank"], "kinds": settings["eval"]["kinds"], "prompts": len(items),
                    "prompt_ids": prompt_ids, "bank_file": bank_name, "bank_file_sha256": bank_sha,
                    "manifest_sha256": manifest_sha},
           "add_sets": block, "costs": {"setup": setup, "forward": forward},
           "provenance": s1.provenance(Path(__file__), settings_sha256, inputs, {})}
    data = canonical_json(doc)
    texts = [item["prompt"] for item in items] + [t for s in sets.values() for _, p, r in s["rows"] for t in (p, r)]
    lc.require_text_free(data, texts, OUTPUT)
    write_atomic(out / OUTPUT, data)
    if sha256_file(out / OUTPUT) != sha256_bytes(data):
        raise s1.Refusal(f"{OUTPUT} did not read back as written")
    return doc, data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--add-set", nargs=3, action="append", default=[], metavar=("NAME", "FILE", "SHA256"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    from experiments.safety_selection.loaders import real_loaders

    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        given = [(name, Path(path), sha) for name, path, sha in args.add_set]
        doc, data = run(args.prepared, args.recipe, given, args.out, real_loaders(), settings, digest)
    except s1.Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {OUTPUT} into {args.out} ({sha256_bytes(data)})")
    for name, block in doc["add_sets"].items():
        print(f"  {name}: {block['rows']} rows, {doc['eval']['prompts']} prompts, "
              f"s_max {block['summary']['min']:.6f} to {block['summary']['max']:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
