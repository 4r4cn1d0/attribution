"""The engine's evaluation path, symbol by symbol (stdlib only; outside the engine's code identity; GI III round 5,
baseline reuse across engine identities).

    python3 scripts/evaluation_path.py symbols [ENGINE_DIR]            print every top-level symbol's SHA-256
    python3 scripts/evaluation_path.py certify BASE_SYMBOLS.json [ENGINE_DIR]
                                                                       the symbols that differ from a base, each
                                                                       checked against TRAINING_ONLY; exit 1 if any
                                                                       evaluation-path symbol differs
    python3 scripts/evaluation_path.py certificate BASE_SYMBOLS.json BASE_IDENTITY.json OUT.json
                                                                       write the evaluation-equivalence certificate
                                                                       for (base engine, this engine): refused unless
                                                                       the evaluation path is unchanged

A symbol is a top-level function or class, each method of a class (Class.method), a top-level assignment (by its
target names), an import statement (by its text), the module docstring, or any other top-level statement (by its
text; an import is keyed by its module). Its hash is the SHA-256 of its exact source text. An import from a module
that is wholly training-only is training-only too. The engine files are the code identity's files: the
top-level .py files of experiments/safety_selection (tests excluded).

TRAINING_ONLY names, per file, the symbols that may differ between two engines whose evaluation outputs are the same:
the training step and its accumulation (engine.py), the training loop and the attribution job (runner.py), the
recipe validation and the loss constants (config.py), and every symbol of attribution.py (the Stage B attribution
features; no evaluation output reads them). A symbol is on the evaluation path unless it is listed here. A file
missing on either side, or any other differing symbol, means the evaluation path may differ: a baseline evaluated
by one engine is then not reused by another.
"""
import ast, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parent / "experiments" / "safety_selection"
WHOLE_FILE = "*"
TRAINING_ONLY = {
    "engine.py": {"<docstring>", "__all__", "EXAMPLE_MEAN,TOKEN_MEAN", "LOSS_WEIGHTINGS", "SCHEDULES", "learning_rate", "accumulate_gradients",
                  "train_step"},
    "runner.py": {"_train_segment", "attributes"},
    "config.py": {"<docstring>", "LOSS", "LOSS_TOKEN_MEAN", "LOSS_WEIGHTINGS", "validate_recipe"},
    "attribution.py": {WHOLE_FILE},
}


def engine_files(engine: pathlib.Path) -> list[pathlib.Path]:
    return sorted(p for p in engine.glob("*.py"))


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def symbols_of(source: str) -> dict[str, str]:
    tree = ast.parse(source)
    out: dict[str, str] = {}
    for k, node in enumerate(tree.body):
        text = ast.get_source_segment(source, node) or ""
        if k == 0 and isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) \
                and isinstance(node.value.value, str):
            out["<docstring>"] = _digest(text)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = _digest(text)
        elif isinstance(node, ast.ClassDef):
            rest = []
            for item in node.body:
                piece = ast.get_source_segment(source, item) or ""
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[f"{node.name}.{item.name}"] = _digest(piece)
                else:
                    rest.append(piece)
            header = [ast.get_source_segment(source, d) or "" for d in node.decorator_list]
            out[node.name] = _digest("\n".join(header + [node.name] + [ast.unparse(b) for b in node.bases] + rest))
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = ",".join(sorted(n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)))
            out[names or f"<assign:{_digest(text)[:16]}>"] = _digest(text)
        elif isinstance(node, ast.ImportFrom):
            out[f"<import from {'.' * node.level}{node.module or ''}:{_digest(text)[:16]}>"] = _digest(text)
        elif isinstance(node, ast.Import):
            out[f"<import {','.join(a.name for a in node.names)}:{_digest(text)[:16]}>"] = _digest(text)
        else:
            out[f"<stmt:{_digest(text)[:16]}>"] = _digest(text)
    return out


def symbols(engine: pathlib.Path = ENGINE) -> dict[str, dict[str, str]]:
    return {p.name: symbols_of(p.read_text(encoding="utf-8")) for p in engine_files(engine)}


def _allowed(file: str, symbol: str) -> bool:
    """A training-only symbol of FILE, or an import from a module that is wholly training-only."""
    allowed = TRAINING_ONLY.get(file, set())
    if WHOLE_FILE in allowed or symbol in allowed:
        return True
    whole = [name[:-3] for name, symbols in TRAINING_ONLY.items() if WHOLE_FILE in symbols]
    return any(symbol.startswith(f"<import from .{module}:") for module in whole)


def certify(base: dict[str, dict[str, str]], new: dict[str, dict[str, str]]) -> dict:
    """Every differing symbol, and whether each is training-only."""
    changed, outside = {}, []
    for name in sorted(set(base) | set(new)):
        if name not in base or name not in new:
            changed[name] = ["<whole file added or removed>"]
            if WHOLE_FILE not in TRAINING_ONLY.get(name, set()):
                outside.append(f"{name}:<whole file>")
            continue
        a, b = base[name], new[name]
        diff = sorted(s for s in set(a) | set(b) if a.get(s) != b.get(s))
        if diff:
            changed[name] = diff
            outside += [f"{name}:{s}" for s in diff if not _allowed(name, s)]
    return {"changed": changed, "evaluation_path_symbols_changed": outside, "evaluation_path_unchanged": not outside}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["symbols"]:
        print(json.dumps(symbols(pathlib.Path(argv[1]) if len(argv) > 1 else ENGINE), indent=1, sort_keys=True))
        return 0
    if argv[:1] == ["certify"]:
        base = json.loads(pathlib.Path(argv[1]).read_text())
        out = certify(base, symbols(pathlib.Path(argv[2]) if len(argv) > 2 else ENGINE))
        print(json.dumps(out, indent=1))
        return 0 if out["evaluation_path_unchanged"] else 1
    if argv[:1] == ["certificate"]:
        sys.path.insert(0, str(HERE.parent))
        from experiments.safety_selection.common import code_identity
        base_symbols = json.loads(pathlib.Path(argv[1]).read_text())
        base_identity = json.loads(pathlib.Path(argv[2]).read_text())
        out = certify(base_symbols, symbols())
        if not out["evaluation_path_unchanged"]:
            raise SystemExit(f"the evaluation path differs: {out['evaluation_path_symbols_changed']}")
        new = code_identity()
        a, b = base_identity["files"], new["files"]
        record = {"kind": "engine evaluation-path equivalence",
                  "rule": "scripts/evaluation_path.py: every top-level symbol of the engine files that differs between "
                          "the two engines is in TRAINING_ONLY (the training step and its accumulation, the learning-rate "
                          "schedule, the training loop, the attribution job, recipe validation and loss constants, and "
                          "attribution.py); a baseline evaluated by the base engine may then be paired with a fine-tune "
                          "of the new engine (scripts/family_probe_reading.py)",
                  "training_only": {k: sorted(v) for k, v in TRAINING_ONLY.items()},
                  "pairs": [{"base_code_sha256": base_identity["sha256"], "code_sha256": new["sha256"],
                             "changed_files": sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f)),
                             "changed_symbols": out["changed"],
                             "base_symbols_sha256": _digest(json.dumps(base_symbols, sort_keys=True))}]}
        pathlib.Path(argv[3]).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
        print(json.dumps(record["pairs"][0], indent=1))
        return 0
    raise SystemExit("usage: evaluation_path.py symbols [ENGINE_DIR] | certify BASE_SYMBOLS.json [ENGINE_DIR] | "
                     "certificate BASE_SYMBOLS.json BASE_IDENTITY.json OUT.json")


if __name__ == "__main__":
    sys.exit(main())
