"""The shared representation pass (REQ-3; RS B1; SPEC §8; outside the engine identity; CPU-tested, runs on a pod).

One pass of the UNTUNED model (``policy.model.disable_adapter()``; no gradients) serves L1 (REQ-10), S3 (REQ-11),
DataShield-style (REQ-12) and a reproduction of Gate C's representation score. Each training row of the named units, each
anchor of the sealed bank and each row of an optional pool file is encoded as a training row (rows and anchors exactly
as the pinned Gate C script encodes them; pool rows by ``encode_train`` under the recipe's limits) and run in ONE
unbatched forward with ``output_hidden_states=True``.

Model-agnostic (the lead's Part C requirement): the layer count n, the hidden size and the final norm are read from the
loaded model; nothing assumes OLMo-2-1B's 16 layers. Hidden-state index convention (L4), for any n:
index 0 = the embedding output; index i (1 <= i <= n - 1) = the raw output of block i - 1; index n = model.norm(the
output of block n - 1). Block b's output is index b + 1; for b = n - 1 that is the post-final-norm state.

Reads, per encoded row of length L with n_prompt prompt tokens (L3; the row must end with the end-of-turn id):
(a) position L - 1, the end-of-turn token; (b) position L - 2, the last response token (Gate C's read);
(c) the mean over the response tokens, positions n_prompt .. L - 2 (end-of-turn excluded);
(d) position n_prompt - 1, the last templated-prompt token (the end of the assistant header).

Anchor means: per index and read, float64 vectors summed in the bank's file order, then divided (Gate C's rule).
Per row and index the pass stores scalars only, never vectors:
- cos_harmful[i] and cos_safe[i]: torch's cosine_similarity (float64) of reads (a), (b), (c), (d) with each set's mean;
- css[i] (DataShield-style, SPEC §4.4): (read c - read d) . v_hat_i, v_i = harmful mean of read (c) - safe mean of
  read (c), v_hat_i = v_i / ||v_i||.
Per index (from the anchors only): cas[i] = v_i' S_inter v_i / v_i' (S_inter + S_intra) v_i on the 128 anchors' read (b)
states z-scored per dimension (population SD; a dimension with SD 0 is set to 0), classes harmful and safe, computed
as sums of squared projections (SPEC §4.1 Eq. 3-5, "as written").

Gate C reproduction: at (index n, read b) the per-unit means (fsum / count) of cos_harmful, cos_safe and their
difference must equal the pinned script's ``groups`` block byte for byte (canonical JSON); a test checks it on CPU.
The pinned script stays as built (U9). Every (index, read) cell other than an arm's own is report only (L3 (1)).

Outputs into --out (absent or empty): ``representation_rows.jsonl`` (one text-free line per scored row) and
``representation_pass.json`` (layout, the index convention, CAS per index, the Gate C block, pools, costs, provenance).
The settings pin the recipe, the anchor bank, the prepared manifest and transformers 4.56.2. CUDA paths: UNTESTED.

Pool pins (W1-08 (1), the lead's ruling option (a)): a second settings file, ``settings/representation_pools.json``,
hash-pinned by POOL_PINS_SHA256 below, lists the W1-known pools {name: {sha256, items, source}} (the 75-row plant pool
and, if built, the 37-row decoy pool). Its sha256 values stay null until REQ-8's sealed pools exist; the lead fills them
before W1. Every run checks each pool against it: a listed name needs a filled pin with the same SHA-256 and item count;
an unlisted name must not carry a listed pin's SHA-256 (a name and hash that do not match); the name "dev" is refused.
Other pools (the S3 pools) stay named on the command line by SHA-256, through their own sealed records.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, json_line, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "representation_pass.json"
SETTINGS_SHA256 = "a555fd899bd2b5caf8d68fb62578ed2e943977341b5bf2dc2d688dcbd034600b"
SETTINGS_NAME = "representation_pass"
READS = ("a", "b", "c", "d")
SETS = ("harmful", "safe")
ROWS_FILE = "representation_rows.jsonl"
SUMMARY_FILE = "representation_pass.json"
POOL_KIND = "stage1 text pool"
POOL_ID = re.compile(r"^[A-Za-z0-9_.:+\-]{1,160}$")
POOL_PINS_PATH = HERE / "settings" / "representation_pools.json"
POOL_PINS_SHA256 = "1451ba5ec435ecaafebd7749f44b6729e45f2157a69a62c55f35e2bbdbae826b"
POOL_PINS_NAME = "representation_pools"
RESERVED_POOL_NAMES = ("dev",)                                  # the dev rows' source name in every output line


# ----- the model's layout and the reads -------------------------------------------------------------


def base_model(model):
    """The transformers model under a PEFT wrapper (or the model itself)."""
    return model.get_base_model() if hasattr(model, "get_base_model") else model


def layout(model) -> dict:
    """Layer count, hidden size, model type and final norm, read from the model (never assumed)."""
    base = base_model(model)
    config = base.config
    decoder = base.get_decoder()
    n = int(config.num_hidden_layers)
    if len(decoder.layers) != n or not hasattr(decoder, "norm"):
        raise s1.Refusal("the model's decoder does not hold num_hidden_layers blocks and a final norm")
    return {"model_type": str(config.model_type), "n_layers": n, "hidden_size": int(config.hidden_size),
            "final_norm": type(decoder.norm).__name__, "hidden_state_indices": n + 1}


def block_output_index(block: int, n_layers: int) -> int:
    """The hidden-state index of block ``block``'s output (L4); for the last block it is the post-final-norm state."""
    if not 0 <= block < n_layers:
        raise s1.Refusal(f"block {block} is outside 0..{n_layers - 1}")
    return block + 1


def positions(input_ids, n_prompt: int, eos_id: int) -> dict:
    """The four reads' positions (L3); the row must end with the end-of-turn id and hold a response token."""
    length = len(input_ids)
    if length < 3 or input_ids[length - 1] != eos_id:
        raise s1.Refusal("a scored row does not end with the end-of-turn id")
    if not 1 <= n_prompt <= length - 2:
        raise s1.Refusal("a scored row has no prompt token or no response token")
    return {"a": length - 1, "b": length - 2, "c": (n_prompt, length - 1), "d": n_prompt - 1}


def read_states(model, input_ids, n_prompt: int, eos_id: int, device: str, n_layers: int) -> list[dict]:
    """One unbatched forward: per hidden-state index 0..n, the four reads as float64 CPU vectors."""
    import torch

    where = positions(input_ids, n_prompt, eos_id)
    ids = torch.tensor([list(input_ids)], device=device)
    hidden = model(input_ids=ids, output_hidden_states=True).hidden_states
    if len(hidden) != n_layers + 1:
        raise s1.Refusal(f"the model returned {len(hidden)} hidden states, not n + 1 = {n_layers + 1}")
    out = []
    for h in hidden:
        h = h[0].to(torch.float64).cpu()
        start, end = where["c"]
        out.append({"a": h[where["a"]], "b": h[where["b"]], "c": h[start:end].mean(dim=0), "d": h[where["d"]]})
    return out


def anchor_means(states: list[list[dict]]) -> list[dict]:
    """Per index and read: the sum of the anchors' vectors in file order, then divided by the count (Gate C's rule)."""
    means = []
    for index in range(len(states[0])):
        per_read = {}
        for read in READS:
            total = None
            for anchor in states:
                v = anchor[index][read]
                total = v if total is None else total + v
            per_read[read] = total / len(states)
        means.append(per_read)
    return means


def cas(harmful: list, safe: list, direction) -> float | None:
    """DataShield's CAS on read (b) states: v' S_inter v / v' (S_inter + S_intra) v after a per-dimension z-score over
    both classes (population SD; SD 0 -> 0); None when the denominator is 0."""
    import torch

    x = torch.stack(list(harmful) + list(safe))
    mu, sd = x.mean(dim=0), x.std(dim=0, correction=0)
    z = torch.where(sd > 0, (x - mu) / torch.where(sd > 0, sd, torch.ones_like(sd)), torch.zeros_like(x))
    zh, zs = z[:len(harmful)], z[len(harmful):]
    grand = z.mean(dim=0)
    inter = intra = 0.0
    for cls in (zh, zs):
        centre = cls.mean(dim=0)
        inter += len(cls) * float(torch.dot(centre - grand, direction)) ** 2
        intra += float(((cls - centre) @ direction).pow(2).sum())
    return inter / (inter + intra) if inter + intra > 0 else None


def cosine(v, mean) -> float:
    import torch

    return float(torch.nn.functional.cosine_similarity(v, mean, dim=0))


# ----- inputs ----------------------------------------------------------------------------------------


def installed_transformers_version() -> str:
    """The version of the transformers module that is imported now."""
    import transformers

    return transformers.__version__


def check_transformers(settings: dict) -> str:
    version = installed_transformers_version()
    if version != settings["transformers_version"]:
        raise s1.Refusal(f"transformers is {version}, the settings pin {settings['transformers_version']}")
    return version


def read_pool(path: Path, digest: str) -> dict:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"a pool file cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"a pool file hashes to {sha256_bytes(data)}, expected {digest}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != POOL_KIND or doc.get("version") != 1:
        raise s1.Refusal("a pool file is not a version-1 stage-1 text pool")
    items = doc.get("items")
    if not isinstance(items, list) or not items or not isinstance(doc.get("name"), str) or not POOL_ID.match(doc["name"]):
        raise s1.Refusal("a pool file needs a name and a non-empty item list")
    if any(not isinstance(i, dict) or set(i) != {"id", "prompt", "response"} or not isinstance(i["prompt"], str)
           or not isinstance(i["response"], str) for i in items):
        raise s1.Refusal("pool items must be {id, prompt, response} with a text prompt and response")
    ids = [i["id"] for i in items]
    if any(not isinstance(x, str) or not POOL_ID.match(x) for x in ids) or len(set(ids)) != len(ids):
        raise s1.Refusal("pool items need distinct short ids")
    return {"name": doc["name"], "sha256": digest, "items": items}


def check_pool_pins(doc) -> dict:
    """The pool-pins document (a stage-1 settings file of its own name), checked: each listed pool has a source, an item
    count and a SHA-256 or null (not filled yet); the filled SHA-256 values are distinct; no pool is named "dev"."""
    s1.check_settings(doc, POOL_PINS_NAME)
    pools = doc.get("pools")
    if not isinstance(pools, dict) or not pools:
        raise s1.Refusal("the pool pins list no pool")
    for name, entry in pools.items():
        if not POOL_ID.match(name) or name in RESERVED_POOL_NAMES:
            raise s1.Refusal(f"the pool pins list a pool named {name!r}")
        if not isinstance(entry, dict) or set(entry) != {"sha256", "items", "source"} or \
                not isinstance(entry["source"], str) or not entry["source"] or \
                isinstance(entry["items"], bool) or not isinstance(entry["items"], int) or entry["items"] < 1 or \
                not (entry["sha256"] is None or (isinstance(entry["sha256"], str) and s1.HEX64.match(entry["sha256"]))):
            raise s1.Refusal(f"the pool pins entry {name} is not {{sha256: hex or null, items: count, source}}")
    filled = [e["sha256"] for e in pools.values() if e["sha256"] is not None]
    if len(set(filled)) != len(filled):
        raise s1.Refusal("two pool pins name one SHA-256")
    return doc


def load_pool_pins(path: Path = POOL_PINS_PATH, expected_sha256: str = POOL_PINS_SHA256) -> tuple[dict, str]:
    """The committed pool pins, refused unless the file hashes to the literal pin (then check_pool_pins)."""
    try:
        doc, digest = s1.load_settings(path, expected_sha256, POOL_PINS_NAME)
    except OSError as exc:
        raise s1.Refusal(f"the pool pins cannot be read ({type(exc).__name__})") from None
    return check_pool_pins(doc), digest


def pin_of(pool: dict, pins: dict) -> str:
    """How the pool is pinned: "pool pins" (a listed W1-known pool whose SHA-256 and item count match its filled pin)
    or "command line" (an unlisted pool, named only by the SHA-256 given with it). Refuses the name "dev", a listed
    pool whose pin is null or differs, and an unlisted name carrying a listed pin's SHA-256."""
    name, listed = pool["name"], pins["pools"]
    if name in RESERVED_POOL_NAMES:
        raise s1.Refusal(f"a pool may not be named {name!r}: it is the dev rows' source name")
    entry = listed.get(name)
    if entry is None:
        other = sorted(n for n, e in listed.items() if e["sha256"] == pool["sha256"])
        if other:
            raise s1.Refusal(f"pool {name} is the file the pool pins list as {other[0]}: the name and hash do not match")
        return "command line"
    if entry["sha256"] is None:
        raise s1.Refusal(f"pool {name} is a W1-known pool whose pin is not filled yet (settings/representation_pools.json)")
    if entry["sha256"] != pool["sha256"]:
        raise s1.Refusal(f"pool {name} hashes to {pool['sha256']}, the pool pins name {entry['sha256']}")
    if entry["items"] != len(pool["items"]):
        raise s1.Refusal(f"pool {name} holds {len(pool['items'])} items, the pool pins say {entry['items']}")
    return "pool pins"


def inputs(prepared_dir: Path, recipe_path: Path, anchors_path: Path, settings: dict):
    """The checked recipe, prepared view, anchors and units, against the settings' pins (ids and hashes only)."""
    from experiments.safety_selection.config import config_sha256, load_recipe
    from experiments.safety_selection.jobs import JobError, read_anchor_bank
    from experiments.safety_selection.prepare import load_prepared, read_manifest

    pins = settings["pins"]
    recipe = load_recipe(recipe_path)
    if config_sha256(recipe) != pins["recipe_sha256"]:
        raise s1.Refusal(f"the recipe hashes to {config_sha256(recipe)}, the settings pin {pins['recipe_sha256']}")
    model_pin = {"repo_id": recipe["model"]["repo_id"], "revision": recipe["model"]["revision"]}
    if model_pin != pins["model"]:
        raise s1.Refusal("the recipe names another model or revision than the settings")
    bank = recipe["attribution"]["query_bank"]
    if bank != "anchors-" + pins["anchor_bank_sha256"]:
        raise s1.Refusal("the recipe's anchor bank is not the pinned one")
    try:
        anchors = read_anchor_bank(anchors_path, bank, recipe)
    except JobError as exc:
        raise s1.Refusal(f"the anchor file is refused ({type(exc).__name__})") from None
    manifest, manifest_sha = read_manifest(prepared_dir, None)
    if manifest_sha != pins["prepared_manifest_sha256"]:
        raise s1.Refusal(f"the prepared manifest is {manifest_sha}, the settings pin {pins['prepared_manifest_sha256']}")
    prepared = load_prepared(prepared_dir, manifest_sha)
    units = sorted(prepared.groups["dev"])
    return recipe, prepared, manifest_sha, anchors, units


# ----- the pass ---------------------------------------------------------------------------------------


def run(prepared_dir: Path, recipe_path: Path, anchors_path: Path, loaders, settings: dict, settings_sha256: str,
        pools: list[tuple[Path, str]] = (), score_units: bool = True,
        pool_pins: tuple[dict, str] | None = None) -> dict[str, bytes]:
    """Every output file of the pass (nothing is written here; the policy load's ledger goes to a scratch folder that
    lives for the whole pass). pool_pins = (document, SHA-256); None loads the committed file by its literal pin."""
    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        return _run(prepared_dir, recipe_path, anchors_path, loaders, settings, settings_sha256, pools, score_units,
                    pool_pins, Path(scratch))


def _run(prepared_dir: Path, recipe_path: Path, anchors_path: Path, loaders, settings: dict, settings_sha256: str,
         pools, score_units: bool, pool_pins, scratch: Path) -> dict[str, bytes]:
    import torch

    from experiments.safety_selection import runner
    from experiments.safety_selection.ledger import RunLedger
    from experiments.safety_selection.textproc import encode_train

    s1.check_settings(settings, SETTINGS_NAME)
    if not score_units and not pools:
        raise s1.Refusal("nothing to score: no dev units and no pool")
    pins, pins_sha256 = load_pool_pins() if pool_pins is None else (check_pool_pins(pool_pins[0]), pool_pins[1])
    version = check_transformers(settings)
    try:
        recipe, prepared, manifest_sha, anchors, units = inputs(prepared_dir, recipe_path, anchors_path, settings)
    except OSError as exc:
        raise s1.Refusal(f"an input file cannot be read ({type(exc).__name__})") from None
    pool_docs = [read_pool(path, digest) for path, digest in pools]
    if len({p["name"] for p in pool_docs}) != len(pool_docs):
        raise s1.Refusal("two pools share one name")
    pinned_by = {p["name"]: pin_of(p, pins) for p in pool_docs}
    started = time.monotonic()
    session = runner.Session(recipe, loaders)
    ledger = RunLedger(scratch, sync=session.sync, memory=session.memory)
    policy = session.policy(ledger, scratch)
    codec, device, model = policy.codec, policy.device, policy.model
    lay = layout(model)
    n = lay["n_layers"]
    sets = runner.anchor_examples(codec, anchors, recipe)
    rows = {}
    if score_units:
        for gid in units:
            for rid in prepared.groups["dev"][gid]:
                rows[rid] = ("dev", gid, runner._verified_example(codec, rid, prepared.train_rows[rid], recipe))
    refused: dict[str, dict[str, int]] = {}
    for pool in pool_docs:
        refused[pool["name"]] = {}
        for item in pool["items"]:
            if item["id"] in rows:
                raise s1.Refusal(f"pool {pool['name']}: an item id repeats a scored id")
            try:
                ex = encode_train(codec, item["id"], item["prompt"], item["response"], recipe["model"]["max_train_tokens"])
            except ValueError as exc:
                reason = type(exc).__name__
                refused[pool["name"]][reason] = refused[pool["name"]].get(reason, 0) + 1
                continue
            rows[item["id"]] = (pool["name"], None, ex)
    setup_seconds = time.monotonic() - started

    was_training = model.training
    model.eval()
    try:
        with torch.no_grad(), model.disable_adapter():                     # the untuned model
            started = time.monotonic()
            anchor_states = {name: [read_states(model, ex.input_ids, ex.n_prompt, codec.eos_id, device, n)
                                    for ex in sets[name]] for name in SETS}
            means = {name: anchor_means(anchor_states[name]) for name in SETS}
            directions, cas_values, v_norms = [], [], []
            for i in range(n + 1):
                v = means["harmful"][i]["c"] - means["safe"][i]["c"]
                norm = float(v.norm())
                v_norms.append(norm)
                directions.append(v / norm if norm > 0 else None)
                cas_values.append(cas([s[i]["b"] for s in anchor_states["harmful"]],
                                      [s[i]["b"] for s in anchor_states["safe"]], v) if norm > 0 else None)
            anchor_seconds = time.monotonic() - started
            started = time.monotonic()
            lines, per_unit = [], {g: [] for g in units}
            for rid, (source, gid, ex) in rows.items():
                states = read_states(model, ex.input_ids, ex.n_prompt, codec.eos_id, device, n)
                cos_h = [[cosine(states[i][r], means["harmful"][i][r]) for r in READS] for i in range(n + 1)]
                cos_s = [[cosine(states[i][r], means["safe"][i][r]) for r in READS] for i in range(n + 1)]
                css = [float(torch.dot(states[i]["c"] - states[i]["d"], directions[i])) if directions[i] is not None
                       else None for i in range(n + 1)]
                lines.append({"id": rid, "source": source, "unit": gid, "n_prompt": ex.n_prompt,
                              "n_tokens": len(ex.input_ids), "cos_harmful": cos_h, "cos_safe": cos_s, "css": css})
                if gid is not None:
                    b = READS.index("b")
                    per_unit[gid].append((cos_h[n][b], cos_s[n][b], cos_h[n][b] - cos_s[n][b]))
            row_seconds = time.monotonic() - started
    finally:
        model.train(was_training)
    gate_c = {gid: {"rows": len(v), "harmful": math.fsum(x[0] for x in v) / len(v),
                    "safe": math.fsum(x[1] for x in v) / len(v), "score": math.fsum(x[2] for x in v) / len(v)}
              for gid, v in per_unit.items() if v}
    rows_bytes = b"".join(json_line(line) for line in lines)
    tokens = sum(len(ex.input_ids) for _, _, ex in rows.values()) + sum(len(e.input_ids) for s in sets.values() for e in s)
    summary = {
        "kind": "stage1 representation pass", "version": 1, "requirement": settings["requirement"],
        "layout": lay, "index_convention": settings["index_convention"], "reads": settings["reads"],
        "untuned": "policy.model.disable_adapter() under torch.no_grad()", "transformers_version": version,
        "anchors": {name: len(sets[name]) for name in SETS},
        "datashield": {"cas": cas_values, "direction_norm": v_norms, "rule": settings["datashield"]},
        "gate_c": {"index": n, "read": "b", "groups": gate_c,
                   "rule": "per unit: fsum / count of cos_harmful, cos_safe and their difference at (index n, read b)"},
        "rows": {"file": ROWS_FILE, "sha256": sha256_bytes(rows_bytes), "lines": len(lines),
                 "by_source": {src: sum(1 for l in lines if l["source"] == src) for src in sorted({l["source"] for l in lines})}},
        "pools": [{"name": p["name"], "sha256": p["sha256"], "items": len(p["items"]), "pinned_by": pinned_by[p["name"]],
                   "refused_by_reason": dict(sorted(refused[p["name"]].items()))} for p in pool_docs],
        "pool_pins": {"file": "settings/representation_pools.json", "sha256": pins_sha256,
                      "filled": sorted(n for n, e in pins["pools"].items() if e["sha256"] is not None),
                      "not_filled": sorted(n for n, e in pins["pools"].items() if e["sha256"] is None)},
        "costs": {"device": device, "setup_seconds": setup_seconds, "anchor_seconds": anchor_seconds,
                  "row_seconds": row_seconds, "tokens": tokens, "forwards": len(rows) + sum(len(s) for s in sets.values()),
                  "peak_memory_bytes": int(torch.cuda.max_memory_allocated()) if device == "cuda" else None},
        "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                    {"prepared_manifest": manifest_sha, "anchor_file": sha256_file(anchors_path),
                                     "recipe_file": sha256_file(recipe_path), "pool_pins": pins_sha256,
                                     **{f"pool_{p['name']}": p["sha256"] for p in pool_docs}},
                                    settings["label_entries"])}
    return {ROWS_FILE: rows_bytes, SUMMARY_FILE: canonical_json(summary)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--pool", action="append", default=[], help="PATH:SHA256 of a stage-1 text pool (repeatable)")
    parser.add_argument("--pools-only", action="store_true", help="score the pools only, not the dev units")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    parser.add_argument("--pool-pins", type=Path, default=POOL_PINS_PATH, help="checked against POOL_PINS_SHA256")
    args = parser.parse_args(argv)
    try:
        try:
            settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        except OSError as exc:
            raise s1.Refusal(f"the settings cannot be read ({type(exc).__name__})") from None
        pins = load_pool_pins(args.pool_pins)
        pools = []
        for spec in args.pool:
            path, _, sha = spec.rpartition(":")
            if not path or not s1.HEX64.match(sha):
                raise s1.Refusal("each --pool is PATH:SHA256 (64 lowercase hex digits)")
            pools.append((Path(path), sha))
        if args.pools_only and not pools:
            raise s1.Refusal("nothing to score: --pools-only with no --pool")
        from experiments.safety_selection.loaders import real_loaders

        files = run(args.prepared.resolve(), args.recipe.resolve(), args.anchors.resolve(), real_loaders(), settings,
                    digest, pools, score_units=not args.pools_only, pool_pins=pins)
        written = s1.write_new_files(args.out.resolve(), files)
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    print(f"wrote {len(written)} files into {args.out}")
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
