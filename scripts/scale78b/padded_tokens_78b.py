"""The $0 padded-tokens tool of one 7-8B family (Mac; no model, no network; counts and hashes only; GXB R-46).

    PY -I -B scripts/scale78b/padded_tokens_78b.py --family F --prepared P_F [--recipe MAIN_F]
        --edit PATH:SHA256 [--edit PATH:SHA256 ...] [--recorded-by WHO] --out REC.json
    PY -I -B scripts/scale78b/padded_tokens_78b.py --check-a0 --family F --prepared P_F [--recipe MAIN_F] --out CHECK.json

What it computes. For each block A and B edit file, the padded tokens per step that the engine trains on, under MAIN_F's
training settings, on P_F (Part 2 section 2.1: train_scale's input; KCR:104). It runs the engine's own code, as an arm
job of that edit does (R: experiments/safety_selection/runner.py):

- every training row encoded by ``runner._verified_example`` (runner.py:164, :200-205: ``encode_train`` at
  ``model.max_train_tokens``, checked token for token against P_F's audit);
- the edit read once by path, refused unless its bytes hash to the SHA-256 named, then ``edits.parse_edit`` (the
  checks of ``edits.load_edit``, edits.py:169-176) and ``edits.edited_corpus`` (runner.py:420);
- the stream ``stream.make_plan`` with the edit's removed and added rows and its hash (runner.py:426-427; a0:
  runner.py:424), iterated by ``plan.iterate`` over steps 1..S of the e1 checkpoint (runner.py:525);
- each step's padded tokens as the engine counts them (runner.py:544-545): per micro-batch of
  ``micro_batch`` consecutive examples (``stream.micro_batches``), its rows times its longest row's input tokens.

S = ceil(rows / 128) (GXB O1): the stream's steps per epoch, which must equal ceil(rows / 128) and the e1 checkpoint's
step; MAIN_F's micro_batch x grad_accum must be 128. An edit's value is the sum of its S steps' padded tokens divided
by S, at each seed 1101-1113 (every seed blocks A and B train at: method arms and a0 from 1101-1107, R_d4-R_d13 at
1104-1113); the row order (and so the pairing of rows into micro-batches) depends on the seed, so the record's value is
the largest over the thirteen seeds (lead ruling P-1 as corrected by R-54), and its ``source`` names the seeds, the rule,
every seed's total and whether the totals differ.

The record (K2's form, R: runkit/stage1-78b/plan_tool.py:3725-3732, read by ``plan_tool.padded_tokens``, :4009-4035):
exactly {kind "stage1-78b padded tokens record", version 1, family, edits {edit SHA-256: padded tokens per step}, source,
utc, recorded_by}. ``source`` is an object: the tool's SHA-256, MAIN_F's path and config_sha256 and training settings,
P_F's manifest, the tokenizer, the engine files' SHA-256, the seeds and the rule, and per edit its rows, steps, removed,
added and rewritten counts and per-seed totals (GXB R-46: MAIN_F's hash and per edit rows, steps and padded tokens).

--check-a0 (lead ruling P-2): the same count on the unedited training set (a0: no edit), at every seed 1101-1113, and
the comparison at seed 1103 with the kit's ``A0_PADDED_TOKENS_PER_STEP`` basis (R: runkit/stage1-78b/rules_78b.py:295
and :308, KCR:104): OLMo-2-7B 1,457,026 padded tokens over 38 steps (38,342.79), Llama-3.1-8B 1,569,846 over 38 steps
(41,311.74). It lists every seed whose a0 value is smaller than seed 1103's (R-58: informational; the exit code does not
change). It writes a check record of its own kind (never a padded-tokens record) and decides nothing.

Every input is named by path and pinned: MAIN_F by its config_sha256 (the family's pin), P_F by its manifest pin (the
engine's ``prepare.load_prepared``), each edit by PATH:SHA256 (an edit whose bytes differ refuses). The tokenizer is the
manifest's, as ``scripts/stage1/build_s_pool.real_codec`` builds it, and must be the recipe's (encode_count_78b's
``real_context`` and ``check_tokenizer``). Output: one canonical JSON record at --out, created once and complete or not
at all (encode_count_78b's ``write_once``), never inside an input's folder or P_F, and never at a symbolic link
(refused before ``out_ok`` resolves the path; R-72). No prompt or response text reaches
stdout, stderr, the record or a message: every output and message is scanned against every text read (P_F's rows and
the edits' texts), and a message that could hold text is replaced by its exception's class name.

Exit 0: written (the check: the a0 value at 1103 equals the basis); 1: the check written, and the a0 value at 1103
differs from the basis; 2: refused, nothing written.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.scale78b import encode_count_78b as ec  # noqa: E402

Refusal = ec.Refusal
KIND = "stage1-78b padded tokens record"                 # R: runkit/stage1-78b/plan_tool.py:3731 PADDED_TOKENS_KIND
KEYS = ("kind", "version", "family", "edits", "source", "utc", "recorded_by")   # R: plan_tool.py:3732
CHECK_KIND = "stage1-78b padded tokens a0 check"
FAMILIES = ec.FAMILIES
SEEDS = tuple(range(1101, 1114))                         # R-54 (P-1 corrected): the largest over seeds 1101-1113
ROWS_PER_STEP = 128                                      # GXB O1 (P1 section 10): ceil(rows / 128) steps
TARGET = "e1"                                            # the arm jobs' target checkpoint: one epoch
RULE = ("padded tokens per step = the engine's padded tokens (runner._train_segment, runner.py:544-545: per "
        "micro-batch of micro_batch consecutive examples, its rows times its longest row's input tokens) summed over "
        "the e1 steps 1..S of the edit's stream (stream.make_plan with the edit's removed and added rows), divided by "
        "S = ceil(rows / 128) (GXB O1); the value is the largest over seeds 1101-1113 (lead ruling P-1 as corrected by "
        "R-54: every seed blocks A and B train at, R_d4-R_d13 at 1104-1113 included), because the row order, and so "
        "each micro-batch's rows, depends on the seed")
# The a0 basis of the kit's A0_PADDED_TOKENS_PER_STEP (R: runkit/stage1-78b/rules_78b.py:295, :308; KCR:104; lead
# ruling P-2): (seed, padded tokens over the steps, steps, padded tokens per step as the kit prints it).
A0_BASIS = {"olmo2-7b": (1103, 1457026, 38, 38342.79), "llama31-8b": (1103, 1569846, 38, 41311.74)}
ENGINE_FILES = ("experiments/safety_selection/runner.py", "experiments/safety_selection/stream.py",
                "experiments/safety_selection/edits.py", "experiments/safety_selection/textproc.py")
EXIT_OK, EXIT_DIFFERS, EXIT_REFUSED = 0, 1, 2


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ----- the engine's view ------------------------------------------------------------------------------------------


def real_loader(prepared: Path, manifest_sha256: str) -> Any:
    """P_F through the engine's own reader at its manifest pin (no bank; the hidden bank is never read)."""
    from experiments.safety_selection.prepare import load_prepared

    try:
        return load_prepared(prepared, manifest_sha256)
    except Exception as exc:          # DataError, OSError, ValueError: the class name only
        raise Refusal(f"the prepared set cannot be loaded at its manifest pin ({type(exc).__name__})") from None


def train_settings(recipe: Mapping[str, Any]) -> dict:
    """MAIN_F's micro_batch and grad_accum (128 rows a step, GXB O1) and its e1 checkpoint (one epoch)."""
    from experiments.safety_selection.config import checkpoint_table

    train = recipe["train"]
    micro, accum = train["micro_batch"], train["grad_accum"]
    if micro * accum != ROWS_PER_STEP:
        raise Refusal(f"MAIN_F trains {micro} x {accum} rows a step, not {ROWS_PER_STEP} (GXB O1)")
    table = dict(checkpoint_table(recipe))
    if table.get(TARGET) != Fraction(1):
        raise Refusal(f"MAIN_F has no {TARGET} checkpoint at one epoch")
    return {"micro_batch": micro, "grad_accum": accum, "max_train_tokens": recipe["model"]["max_train_tokens"],
            "target_checkpoint": TARGET}


def encoded_corpus(prepared: Any, codec: Any, recipe: Mapping[str, Any], guard: ec.TextGuard) -> dict:
    """Every training row as the engine encodes and audits it (runner.py:164, :200-205)."""
    from experiments.safety_selection.runner import _verified_example

    for row in prepared.train_rows.values():
        guard.add(row.get("prompt"), row.get("response"))
    try:
        return {rid: _verified_example(codec, rid, row, recipe) for rid, row in sorted(prepared.train_rows.items())}
    except Exception as exc:
        raise Refusal(f"a training row does not encode as P_F's audit says ({type(exc).__name__})") from None


def read_edit(path: Path, pin: str, prepared: Any, guard: ec.TextGuard) -> Any:
    """The edit read once by path; its bytes must hash to ``pin``; then the engine's parse_edit (load_edit's checks)."""
    from experiments.safety_selection.edits import EditError, parse_edit

    data = ec.read_pinned(path, pin, f"the edit {pin[:12]}...")
    try:
        doc = json.loads(data)
        for item in doc.get("add", []) if isinstance(doc, dict) and isinstance(doc.get("add"), list) else []:
            if isinstance(item, dict):
                guard.add(item.get("prompt"), item.get("response"))
        for item in doc.get("rewrite", []) if isinstance(doc, dict) and isinstance(doc.get("rewrite"), list) else []:
            if isinstance(item, dict):
                guard.add(item.get("response"))
        if isinstance(doc, dict):
            guard.add(doc.get("name"))
    except ValueError:
        pass                                    # parse_edit refuses it below
    try:
        return parse_edit(data, prepared)
    except EditError as exc:
        raise Refusal(f"the edit {pin[:12]}... is refused by the engine's parse_edit: {exc}") from None


def plan_for(prepared: Any, settings: Mapping[str, Any], seed: int, edit: Any = None) -> Any:
    """The engine's stream for one run (runner.py:422-427)."""
    from experiments.safety_selection.stream import make_plan

    if edit is None:
        return make_plan(prepared.corpus, [], seed, settings["micro_batch"], settings["grad_accum"])
    return make_plan(prepared.corpus, sorted(edit.removed), seed, settings["micro_batch"], settings["grad_accum"],
                     edit.added_ids, edit.sha256)


def steps_of(plan: Any) -> int:
    """S = ceil(rows / 128) (GXB O1): the stream's steps per epoch, which must be the e1 checkpoint's step."""
    rows = plan.retained
    steps = -(-rows // ROWS_PER_STEP)
    if plan.steps_per_epoch != steps or plan.checkpoint(Fraction(1))["step"] != steps:
        raise Refusal(f"the stream's {plan.steps_per_epoch} steps are not ceil({rows} / {ROWS_PER_STEP}) = {steps}")
    return steps


def padded_total(plan: Any, corpus: Mapping[str, Any], micro_batch: int) -> tuple[int, int]:
    """(the padded tokens summed over the e1 steps, the steps), each step counted as runner.py:544-545 counts it."""
    from experiments.safety_selection.stream import micro_batches

    steps, total = steps_of(plan), 0
    for step, _epoch, rows in plan.iterate(1, steps):
        if not rows or any(r in plan.removed for r in rows):           # runner.py:527
            raise Refusal(f"step {step}: an empty batch or a removed row reached the stream")
        examples = [corpus[r] for r in rows]
        total += sum(len(mb) * max(len(e.input_ids) for e in mb) for mb in micro_batches(examples, micro_batch))
    return total, steps


def seed_totals(prepared: Any, corpus: Mapping[str, Any], settings: Mapping[str, Any], edit: Any = None) -> dict:
    """{seed: padded total} over SEEDS, and the rows and steps (the same at every seed)."""
    totals, shape = {}, None
    for seed in SEEDS:
        plan = plan_for(prepared, settings, seed, edit)
        total, steps = padded_total(plan, corpus, settings["micro_batch"])
        if shape is not None and shape != (plan.retained, steps):
            raise Refusal("the rows or steps differ between seeds")
        shape = (plan.retained, steps)
        totals[seed] = total
    return {"rows": shape[0], "steps": shape[1], "totals": totals}


def per_step(total: int, steps: int) -> float:
    return total / steps


# ----- the two modes ----------------------------------------------------------------------------------------------


def common_source(family: str, recipe_path: str, digest: str, settings: Mapping[str, Any], prepared: Any,
                  tokenizer: Mapping[str, Any]) -> dict:
    return {"tool": "scripts/scale78b/padded_tokens_78b.py", "tool_sha256": sha256_file(Path(__file__)),
            "encode_count_sha256": sha256_file(Path(ec.__file__)),          # R-74: its pins, guard and writer
            "family": family, "recipe": {"path": ec._label(recipe_path), "config_sha256": digest, **settings},
            "manifest_sha256": prepared.manifest_sha256, "tokenizer": dict(tokenizer),
            "engine_files": {p: sha256_file(REPO / p) for p in ENGINE_FILES},
            "seeds": list(SEEDS), "rule": RULE}


def load_inputs(family: str, recipe_arg: Path | None, prepared_path: Path, ctx: ec.Context,
                loader: Callable[[Path, str], Any], guard: ec.TextGuard) -> tuple:
    recipe, digest, recipe_path, _limits = ec.load_recipe(family, recipe_arg)
    settings = train_settings(recipe)
    tokenizer = ec.check_tokenizer(recipe, ctx)
    pin = ec.MANIFESTS[family]
    prepared = loader(prepared_path, pin)
    if prepared.manifest_sha256 != pin or ctx.manifest_sha256 != pin:
        raise Refusal(f"P_F's manifest is not {family}'s pin {pin[:12]}...")
    corpus = encoded_corpus(prepared, ctx.codec, recipe, guard)
    return recipe, digest, recipe_path, settings, tokenizer, prepared, corpus


def run_record(family: str, edits: Sequence[tuple[Path, str]], recipe_arg: Path | None, prepared_path: Path,
               ctx: ec.Context, loader: Callable[[Path, str], Any], guard: ec.TextGuard, recorded_by: str) -> dict:
    if not edits:
        raise Refusal("give every block A and B edit with --edit PATH:SHA256")
    pins = [pin for _, pin in edits]
    if len(set(pins)) != len(pins):
        raise Refusal("an edit SHA-256 is named twice")
    recipe, digest, recipe_path, settings, tokenizer, prepared, corpus = load_inputs(
        family, recipe_arg, prepared_path, ctx, loader, guard)
    values, detail = {}, {}
    for path, pin in edits:
        edit = read_edit(path, pin, prepared, guard)
        try:
            from experiments.safety_selection.edits import edited_corpus

            mine = edited_corpus(corpus, edit, prepared, ctx.codec, settings["max_train_tokens"])
        except Exception as exc:
            raise Refusal(f"the edit {pin[:12]}...'s rows do not encode ({type(exc).__name__})") from None
        out = seed_totals(prepared, mine, settings, edit)
        totals = out["totals"]
        top = max(totals.values())
        values[pin] = per_step(top, out["steps"])
        detail[pin] = {"rows": out["rows"], "steps": out["steps"], "removed": len(edit.removed),
                       "added": len(edit.added), "rewritten": len(edit.rewrite),
                       "padded_tokens_by_seed": {str(s): t for s, t in totals.items()},
                       "largest_at_seed": min(s for s, t in totals.items() if t == top),
                       "seed_dependent": len(set(totals.values())) > 1}
    source = common_source(family, recipe_path, digest, settings, prepared, tokenizer)
    source["edits"] = detail
    return {"kind": KIND, "version": 1, "family": family, "edits": dict(sorted(values.items())), "source": source,
            "utc": utc_now(), "recorded_by": recorded_by}


def run_check(family: str, recipe_arg: Path | None, prepared_path: Path, ctx: ec.Context,
              loader: Callable[[Path, str], Any], guard: ec.TextGuard) -> dict:
    recipe, digest, recipe_path, settings, tokenizer, prepared, corpus = load_inputs(
        family, recipe_arg, prepared_path, ctx, loader, guard)
    out = seed_totals(prepared, corpus, settings)
    seed, basis_total, basis_steps, basis_value = A0_BASIS[family]
    total, steps = out["totals"][seed], out["steps"]
    value = per_step(total, steps)
    matches = total == basis_total and steps == basis_steps and round(value, 2) == basis_value
    return {"kind": CHECK_KIND, "version": 1, "family": family,
            "a0": {"rows": out["rows"], "steps": steps,
                   "padded_tokens_by_seed": {str(s): t for s, t in out["totals"].items()},
                   "per_step_by_seed": {str(s): per_step(t, steps) for s, t in out["totals"].items()},
                   "seed_dependent": len(set(out["totals"].values())) > 1,
                   "smaller_than_basis_seed": [s for s, t in out["totals"].items() if t < total]},   # R-58
            "basis": {"seed": seed, "padded_tokens": basis_total, "steps": basis_steps, "per_step": basis_value,
                      "kit_constant": "runkit/stage1-78b/rules_78b.py FAMILIES[family]['A0_PADDED_TOKENS_PER_STEP']"},
            "at_basis_seed": {"padded_tokens": total, "steps": steps, "per_step": value},
            "matches": matches, "decides": "nothing: the lead compares it with the kit's constant (lead ruling P-2)",
            "source": common_source(family, recipe_path, digest, settings, prepared, tokenizer), "utc": utc_now()}


def summary_lines(doc: Mapping[str, Any]) -> list[str]:
    if doc["kind"] == CHECK_KIND:
        a = doc["at_basis_seed"]
        b = doc["basis"]
        return [f"{doc['family']} a0 check: {a['padded_tokens']} padded tokens over {a['steps']} steps at seed "
                f"{b['seed']} = {a['per_step']:.2f} per step; the basis {b['padded_tokens']} / {b['steps']} = "
                f"{b['per_step']}; matches: {doc['matches']}",
                f"  per seed: {json.dumps(doc['a0']['padded_tokens_by_seed'], sort_keys=True)}",
                f"  seeds whose a0 value is smaller than seed {b['seed']}'s (informational, R-58): "
                f"{doc['a0']['smaller_than_basis_seed'] or 'none'}"]
    lines = [f"{doc['family']} padded tokens per step (largest over seeds {SEEDS[0]}-{SEEDS[-1]}):"]
    for pin, value in doc["edits"].items():
        d = doc["source"]["edits"][pin]
        lines.append(f"  {pin[:16]}... rows {d['rows']} steps {d['steps']}: {value:.2f} (seed {d['largest_at_seed']}; "
                     f"seed dependent: {d['seed_dependent']})")
    return lines


def main(argv: list[str] | None = None, *, context: Callable[[str, Path], ec.Context] | None = None,
         loader: Callable[[Path, str], Any] | None = None) -> int:
    """The command line. ``context`` and ``loader`` are ENGINEERING FIXTURES for tests only (a fake codec, a fixture
    prepared set); the real run uses encode_count_78b.real_context and the engine's load_prepared."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check-a0", action="store_true", help="the a0 count against the kit's basis (P-2)")
    parser.add_argument("--family", required=True, choices=FAMILIES)
    parser.add_argument("--prepared", type=Path, required=True, help="P_F, the family's prepared set folder")
    parser.add_argument("--recipe", type=Path, default=None, help="MAIN_F (default: the family's main recipe path)")
    parser.add_argument("--edit", action="append", default=[], help="PATH:SHA256 of a block A or B edit file")
    parser.add_argument("--recorded-by", default="the lead's token-count step (padded_tokens_78b.py)")
    parser.add_argument("--out", type=Path, required=True, help="the record (a new file)")
    args = parser.parse_args(argv)
    guard = ec.TextGuard()
    try:
        if args.check_a0 and args.edit:
            raise Refusal("--check-a0 counts the unedited training set: it takes no --edit")
        edits = [ec.parse_spec(spec, "--edit") for spec in args.edit]
        if args.out.is_symlink():          # R-72: a symbolic link (dangling, to a file, to itself) before out_ok resolves it
            raise Refusal(f"--out {args.out.name} is a symbolic link: the record is created at its own path, once")
        out = ec.out_ok(args.out, [Path(p).resolve().parent for p, _ in edits] + [args.prepared])
        ctx = (context or ec.real_context)(args.family, args.prepared)
        load = loader or real_loader
        if args.check_a0:
            doc = run_check(args.family, args.recipe, args.prepared, ctx, load, guard)
        else:
            doc = run_record(args.family, edits, args.recipe, args.prepared, ctx, load, guard, args.recorded_by)
        data = ec.canonical(doc)
        lines = summary_lines(doc)
        if guard.hits(data) or any(guard.hits(line) for line in lines):
            raise Refusal("the record or the printout would hold text: nothing written")
        digest = ec.write_once(out, data)
    except (Exception, SystemExit) as exc:     # every refusal and every other error, a SystemExit included: no text
        print(f"REFUSED: {guard.message(exc)} (nothing written)", file=sys.stderr)
        return EXIT_REFUSED
    for line in lines:
        print(line)
    print(f"wrote {out.name} ({digest})")
    if doc["kind"] == CHECK_KIND and not doc["matches"]:
        return EXIT_DIFFERS
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
