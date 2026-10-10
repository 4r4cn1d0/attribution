"""The engine's evaluation path, symbol by symbol (stdlib only; outside the engine's code identity; GI III rounds 5 and
6, baseline reuse across engine identities).

    python3 scripts/evaluation_path.py symbols [ENGINE_DIR]            print every top-level symbol's SHA-256
    python3 scripts/evaluation_path.py certify BASE_SYMBOLS.json [ENGINE_DIR]
                                                                       the symbols that differ from a base, each
                                                                       checked against TRAINING_ONLY; exit 1 if any
                                                                       evaluation-path symbol differs
    python3 scripts/evaluation_path.py certificate OUT.json PAIR [PAIR ...]
                                                                       write the evaluation-equivalence certificate;
                                                                       PAIR = BASE_SYMBOLS,BASE_IDENTITY for (base, this
                                                                       engine), or BASE_SYMBOLS,BASE_IDENTITY,
                                                                       NEW_SYMBOLS,NEW_IDENTITY for two recorded engines;
                                                                       refused unless every pair's evaluation path is
                                                                       unchanged

**Symbols** (``symbols_of``): a top-level function or class with its decorators, each method of a class
(Class.method, with its decorators), a top-level assignment (by its target names), an import (keyed by its module and
each binding as NAME or BOUND=NAME for ``import NAME as BOUND``), the module docstring, or any other top-level statement (by its text). Its hash is the SHA-256 of
its exact source text. Two top-level symbols with one key, or two that bind one name (a def, class, assignment target
or imported name), refuse (the second would hide the first; a rebinding inside another statement is that statement's
own text). Each file also
gets ``<side_effect_free>``: "true" when its top level only holds the docstring, imports, function and class
definitions with plain decorators, and assignments without calls (importing it then only binds names).

**Certification** (``certify``): every symbol that differs between two engines must be (a) listed in TRAINING_ONLY for
its file, each entry justified below, or (b) an import from a side-effect-free engine module whose every binding
either was in the base file already (the same module, name and bound name: a regrouped import) or binds a name that
the base file did not bind and no other top-level symbol of the new file binds, or (c) an import removed whose every
binding the new file still has. A changed binding (``from .a import f`` becoming ``from .b import f``, or
``import g as f``) is outside (b) and (c).
A changed training-only function that writes process-global state (``global_writes``), an import that binds a
builtin's name, a changed code-identity file outside the inventory (the reused minimal_safety modules), a file added or
removed, or any other differing symbol, means the
evaluation path may differ: a baseline evaluated by one engine is then not reused by another. Every listed name must
exist in the current engine (``missing_training_only``).
A symbol may also be listed in REVIEWED (Gate B, brief gate-b-engine-kit-reading-20261008, A1): it is accepted only
when its text hashes at the base and at the new engine equal the entry's (exact text, pair-scoped); a record key
(``<global_writes>``, ``<side_effect_free>``) or an import key can never be REVIEWED.
"""
from __future__ import annotations

import ast, builtins, hashlib, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parent / "experiments" / "safety_selection"
# Each entry may differ between engines whose evaluation outputs are the same. Why each cannot change an output. The
# training functions run in the same process before (and, in the memory preflight, inside) an evaluation job, so each
# reason assumes the function writes no process-global state: ``certify`` refuses a changed entry whose body may
# (``global_writes``: a global or nonlocal statement, a store into an attribute or item of a non-local name, a call
# whose dotted name starts with a GLOBAL_CALLS prefix (the known torch, CUDA, os.environ, sys, random, numpy and
# transformers setters), a mutating method of a non-local object, setattr, exec and the like, or a call of an engine
# function that may itself, transitively), and a changed entry that is an assignment making a call. NOT detected (a
# stated limit): writes through a passed object (the model, the optimizer), a local alias of a global object,
# setters outside GLOBAL_CALLS, and random numbers drawn.
TRAINING_ONLY = {
    "engine.py": {
        "<docstring>",              # documentation
        "__all__",                  # the star-import list; the runner and loaders import the module, never with *
        "EXAMPLE_MEAN,TOKEN_MEAN",  # loss-weighting names, read by the training step and the attribution job only
        "LOSS_WEIGHTINGS",          # the accepted weightings, read by accumulate_gradients only
        "SCHEDULES",                # the accepted schedules, read by learning_rate only
        "accumulate_gradients",     # gradients of the training objective; in an evaluation-only job it runs only in
                                    # the memory preflight, whose adapter is checked unchanged and whose gradients are
                                    # cleared; its outputs are the gradients and losses of training
        "train_step",               # one optimizer update (training only)
        "learning_rate",            # the scheduled rate of a training step (the training loop and the attribution job)
    },
    "runner.py": {
        "_train_segment",           # the training loop; evaluation runs after it on the in-memory policy, so it must
                                    # leave no global state (above); the adapter it trains is the evaluated object
        "attributes",               # the attribution job; it writes attribution outputs only
    },
    "config.py": {
        "<docstring>",              # documentation
        "LOSS_TOKEN_MEAN",          # the token-mean loss text, compared by validate_recipe only
        "validate_recipe",          # recipe validation: it accepts or refuses a recipe and returns nothing used
    },
    "jobs.py": {
        "check_identities",         # job validation: it accepts or refuses a job before any work and computes nothing
    },
    "attribution.py": {
        "<docstring>",              # documentation
        "__all__",                  # the star-import list (unused)
        "ROW_WEIGHTING",            # a text written to the attribution outputs only
        "step_weights",             # the token-mean row weights of the attribution job
        "interval_rates",           # the scheduled-rate rule of the attribution job
        "checkpoint_scores",        # the attribution features of one checkpoint (the attribution job only)
    },
}
# Gate B (brief gate-b-engine-kit-reading-20261008, A1): symbols outside TRAINING_ONLY reviewed by exact text. Each
# entry: "file.py:symbol" -> {"base": its text SHA-256 at e49a978c (null: a new symbol), "new": its text SHA-256 at
# the reviewed engine, "inserted": the exact lines inserted into the base text (every other line unchanged),
# "global_writer": its membership in the file's <global_writes> record at e49a978c, "reason": why it cannot change an
# evaluation output}. Unlike TRAINING_ONLY, an entry allows only the one reviewed text.
REVIEWED: dict[str, dict] = {
    '__main__.py:_make_job': {
        "base": 'f0eaf486bc71f515e5cdaf9989d51efbfd7745c03dd26e9ab7b7b3b4aa262dc0',
        "new": '5da835a4a8140cdfb4d84c3b1ecf8c63e8addde831b53ab533ac2a965345c696',
        "inserted": [
            '        fields["query_bank"] = recipe["attribution"]["query_bank"]     # Gate B A7: the recipe\'s bank',
            '        if args.anchors is not None:',
            '            from .jobs import read_anchor_bank',
            '',
            '            read_anchor_bank(args.anchors, fields["query_bank"], recipe)',
            '            fields["anchors"] = str(args.anchors)',
        ],
        "global_writer": False,
        "reason": "make-job (A7): an attributes job takes the recipe's query bank and, for an anchor bank, the path of the anchor file checked by read_anchor_bank; it writes a job file and evaluates nothing",
    },
    '__main__.py:_parser': {
        "base": '5f95eb5792b091c1527672e0d50d2015f86d01824fc4adffc5f7188241533151',
        "new": '3108cd1034efb550033add3c59142e0201a8b5aa12b2a7d257c4380d604c2d6c',
        "inserted": [
            '    p.add_argument("--anchors", help="attributes: the anchor file of the recipe\'s anchors-<SHA-256> query bank")',
        ],
        "global_writer": False,
        "reason": 'one CLI option, --anchors (A7); argument parsing only',
    },
    'attribution.py:BI_ANCHORED_SIGN': {
        "base": None,
        "new": 'f9e9e318945cbfe34c63d62de6da49398d6de9229c738b37f9d6c336927edc17',
        "inserted": [],
        "global_writer": False,
        "reason": "a text written only into an anchor-bank attribution job's groups.json (A2)",
    },
    'jobs.py:_anchor_attributes_job': {
        "base": None,
        "new": '4223233bbce31deb223674e09d81430ad865c5dcaa44348abbec85e4dd135ce9',
        "inserted": [],
        "global_writer": False,
        "reason": "checks an anchor-bank attributes job's keys (A2); it accepts or refuses and computes nothing",
    },
    'jobs.py:read_anchor_bank': {
        "base": None,
        "new": 'a3d512ef7c2c20a658c06c0c265e17d448cb1c9d2b27bcfe1a1d3f450088a186',
        "inserted": [],
        "global_writer": False,
        "reason": 'reads and checks the anchor file for attributes jobs and make-job (A2); it accepts or refuses and computes nothing an evaluation reads',
    },
    'jobs.py:validate_job': {
        "base": '6e11dc716498331aec4c9cc491df96692398dc207fbd4244cb3530f905479723',
        "new": '8d360ea1c345d45b8c73145208b9c8f3816fb4311d3eb1711ca7432cd421debd',
        "inserted": [
            '    if job["kind"] == "attributes" and "anchors" in job:      # an anchor bank (Gate B, README "Anchor bank")',
            '        expected = expected | {"anchors"}',
            '        if job["query_bank"] != "ref" or "anchors" in job:',
            '            return _anchor_attributes_job(job)',
        ],
        "global_writer": False,
        "reason": 'two inserted pairs (A2): an attributes job may carry anchors, and an anchor-bank attributes job is checked by _anchor_attributes_job; every other kind and key is checked as before',
    },
    'runner.py:_train_and_evaluate': {
        "base": '4dccfa7917d687484dfea1716a0d4235394a980c90ab50e316a56702cc66dd30',
        "new": 'f5e19bba1d11704c88c39b7c94217cfaee3c4386544cafde8d3810839cbc5d39',
        "inserted": [
            '    lock = lock_record(session.device, Path.cwd())                      # Gate B A4: before any model load',
            '    merge_assets(run_dir, lock, guard_pin(recipe) if job["evaluate_bank"] is not None else None)',
        ],
        "global_writer": True,
        "reason": 'two inserted lines (A4): lock_record before the policy loads (one file read; a missing lock refuses on cuda) and merge_assets after assets.json (two added keys and the lock copy); neither touches the model, data, RNG or numeric settings',
    },
    'runner.py:anchor_examples': {
        "base": None,
        "new": '7ac1f8c7360c68ae85aebbcfd04b714b3d31843ac525e5cebafe049626c2bd91',
        "inserted": [],
        "global_writer": False,
        "reason": 'encodes the anchor rows of an attribution job (A2); no evaluation calls it',
    },
    'runner.py:eval_state': {
        "base": 'd9f6721abe1e00e8a5e97e3d72abe04e93d2da953161556e82b0e6f3c1eaccf9',
        "new": 'c36bbd1917046af9b60420f01bf69a4e7f69f2e76e9a133a95ede94e8e686843',
        "inserted": [
            '        lock = lock_record(session.device, Path.cwd())                  # Gate B A4: before any model load',
            '        merge_assets(run_dir, lock, guard_pin(recipe))',
        ],
        "global_writer": True,
        "reason": 'two inserted lines (A4), as in _train_and_evaluate: lock_record before the policy loads and merge_assets after assets.json',
    },
    'runner.py:guard_pin': {
        "base": None,
        "new": '033ba3065093996fd526df3b6d061185915e35584cb2bafe03c93286170ed456',
        "inserted": [],
        "global_writer": False,
        "reason": "lists the guard snapshot's files for assets.json (A4); a directory listing, no model load",
    },
    'runner.py:lock_record': {
        "base": None,
        "new": '5c57d6953b5475f27c359b2b5fabeb325ab4c5e3a9e0531f9ec2a813965a0095',
        "inserted": [],
        "global_writer": False,
        "reason": 'reads environment-linux.lock on cuda and returns its SHA-256 and bytes (A4)',
    },
    'runner.py:merge_assets': {
        "base": None,
        "new": '6ecaad386497d4ccd274a03ba3f832141f63be4c9163e96ecdba514bda0b3738',
        "inserted": [],
        "global_writer": False,
        "reason": 'rewrites assets.json with environment_lock and guard and copies the lock bytes into the unit (A4); it writes only unit records',
    },
}
SIDE_EFFECT_FREE = "<side_effect_free>"
GLOBAL_WRITES = "<global_writes>"
GLOBAL_CALLS = ("torch.backends.", "torch.set_", "torch.use_", "torch.manual_seed", "torch.seed", "torch.cuda.",
                "torch.random.", "torch._C.", "torch.autograd.set_", "torch.autograd.grad_mode.", "os.environ",
                "os.putenv", "os.unsetenv", "sys.", "random.", "np.random.", "numpy.random.", "np.set", "numpy.set",
                "transformers.", "warnings.", "logging.")
NOT_GLOBAL = {"random.Random"}                 # a new generator object, not the global one
READ_ONLY = ("get", "is_")                     # a call whose last name starts so reads state (getstate, get_rng_state)
READ_ONLY_NAMES = {"device_count", "current_device"}
# Engine helpers whose calls leave no global state behind, each for a stated reason (their own bodies are engine
# symbols outside TRAINING_ONLY, so a change to one is refused anyway):
NET_NEUTRAL = {
    "preserved_rng",                           # restores every RNG state it captured, on exit (engine.preserved_rng)
}
CONDITIONAL = {
    "load_state": ("restore_rng_state", False),  # with the RNG restore off it writes only the adapter and optimizer
}                                                # passed to it (engine.load_state)
MUTATORS = {"append", "extend", "insert", "pop", "popitem", "update", "clear", "setdefault", "remove", "add",
            "discard", "sort", "reverse", "__setitem__", "__delitem__"}
GLOBAL_BUILTINS = {"setattr", "delattr", "exec", "eval", "globals", "__import__", "vars"}
IMPORT = re.compile(r"<import from (\.*)(\w*):names=([\w,=]*)>")


class SymbolError(ValueError):
    """Two top-level symbols of one file share a name."""


def engine_files(engine: pathlib.Path) -> list[pathlib.Path]:
    return sorted(p for p in engine.glob("*.py"))


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _Source(str):
    """A file's text whose source segments are cut from one line split (``ast.get_source_segment`` splits the whole
    file again on each call); the same rule: line endings \\r\\n, \\r or \\n, columns as UTF-8 byte offsets."""

    def segment(self, node) -> str | None:
        if getattr(node, "end_lineno", None) is None:
            return None
        lines = self.__dict__.get("lines")
        if lines is None:
            lines = self.__dict__["lines"] = re.findall(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+$", str(self))
        first, last = node.lineno - 1, node.end_lineno - 1
        if first == last:
            return lines[first].encode()[node.col_offset:node.end_col_offset].decode()
        return "".join([lines[first].encode()[node.col_offset:].decode(), *lines[first + 1:last],
                        lines[last].encode()[:node.end_col_offset].decode()])


def _segment(source: str, node) -> str | None:
    return source.segment(node) if isinstance(source, _Source) else ast.get_source_segment(source, node)


def _with_decorators(source: str, node) -> str:
    """The node's own text preceded by each decorator's text (a decorator changes what the name binds)."""
    parts = ["@" + (_segment(source, d) or "") for d in getattr(node, "decorator_list", [])]
    return "\n".join(parts + [_segment(source, node) or ""])


def _no_calls(node) -> bool:
    return not any(isinstance(n, (ast.Call, ast.Await, ast.Yield, ast.YieldFrom)) for n in ast.walk(node))


def side_effect_free(tree: ast.Module) -> bool:
    for k, node in enumerate(tree.body):
        if k == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            plain = all(isinstance(d, (ast.Name, ast.Attribute)) for d in node.decorator_list)
            defaults = all(_no_calls(d) for d in getattr(getattr(node, "args", None), "defaults", []) or [])
            bases = all(_no_calls(b) for b in getattr(node, "bases", []))
            if plain and defaults and bases:
                continue
            return False
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and _no_calls(node):
            continue
        return False
    return True


def _dotted(node) -> str | None:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    return ".".join([node.id, *reversed(parts)]) if isinstance(node, ast.Name) else None


def _root(node) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Starred)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def global_writes(fn, writers: frozenset = frozenset()) -> bool:
    """Whether a function's body may write process-global state (module doc, TRAINING_ONLY): a global or nonlocal
    statement; a store or deletion of an attribute or item whose root is not a local name (any target: assignment,
    loop, with-as, nested unpacking); a call of setattr-like builtins, of a GLOBAL_CALLS prefix, of a mutating method
    (MUTATORS) on a non-local root, or of an engine function in ``writers`` (by name, or by its last component on a
    non-local root: ``en.restore_rng``); read-only calls (READ_ONLY), NET_NEUTRAL helpers and CONDITIONAL calls with
    their stated argument are not writes. Conservative where it is syntactic; blind to writes through a passed object,
    a local alias of a global one (``env = os.environ; env[k] = v``) and setters outside GLOBAL_CALLS."""
    direct, callees = _analysis(fn)
    return direct or bool(callees & writers)


_ANALYSES: dict = {}


_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp,
           ast.GeneratorExp)


def _own_scope(fn):
    """The nodes of a function's own scope (not those of a nested def, class, lambda or comprehension)."""
    stack = list(ast.iter_child_nodes(fn))
    while stack:
        node = stack.pop()
        yield node
        if not isinstance(node, _SCOPES):
            stack.extend(ast.iter_child_nodes(node))


def _chain(node) -> str | None:
    """The dotted name of a callee whose chain passes through items or calls (``LIMITS["a"].append``,
    ``logging.getLogger(x).setLevel``), items and calls dropped; None for a fresh NOT_GLOBAL object or a non-name root."""
    parts = []
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
        if isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        elif isinstance(node, ast.Call):
            if _dotted(node.func) in NOT_GLOBAL:
                return None
            node = node.func
        else:
            node = node.value
    return ".".join([node.id, *reversed(parts)]) if isinstance(node, ast.Name) else None


def _bound_in(scope) -> set[str]:
    """The names a scope binds itself: its arguments, comprehension targets, stores and nested def or class names (an
    import in a body binds a shared module and is never local)."""
    names = {a.arg for a in ast.walk(scope.args) if isinstance(a, ast.arg)} if isinstance(
        getattr(scope, "args", None), ast.arguments) else set()
    for generator in getattr(scope, "generators", []):
        names |= {n.id for n in ast.walk(generator.target) if isinstance(n, ast.Name)}
    for node in _own_scope(scope):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
    return names


def _analysis(fn) -> tuple[bool, frozenset]:
    """(whether the body writes global state itself, the names whose being writers would make it one), once per node.
    Names are resolved lexically: each nested scope sees its own bindings and those of the scopes around it."""
    if fn in _ANALYSES:
        return _ANALYSES[fn]
    state = {"direct": any(isinstance(n, (ast.Global, ast.Nonlocal)) for n in ast.walk(fn)), "callees": set()}

    def check(node, local: set[str]) -> None:
        if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, (ast.Store, ast.Del)) \
                and _root(node) not in local:
            state["direct"] = True
        if not isinstance(node, ast.Call):
            return
        if isinstance(node.func, ast.Call) and _dotted(node.func.func) == "getattr" and node.func.args \
                and _root(node.func.args[0]) not in local:
            state["direct"] = True                 # getattr(module, name)(...): a dynamic call on a global object
            return
        name, through = _dotted(node.func), False
        if name is None:
            name, through = _chain(node.func), True
        if name is None or name in NOT_GLOBAL:
            return
        parts = name.split(".")
        last = parts[-1]
        if through:                                # no callee name: only the prefixes and mutators apply
            if parts[0] not in local and (name.startswith(GLOBAL_CALLS) or last in MUTATORS):
                state["direct"] = True
            return
        if last.startswith(READ_ONLY) or last in READ_ONLY_NAMES or last in NET_NEUTRAL:
            return
        if last in CONDITIONAL and any(k.arg == CONDITIONAL[last][0] and isinstance(k.value, ast.Constant)
                                       and k.value.value is CONDITIONAL[last][1] for k in node.keywords):
            return
        if name in GLOBAL_BUILTINS or name.startswith(GLOBAL_CALLS):
            state["direct"] = True
        elif parts[0] not in local:              # a bare call names its callee; a dotted one by its last name
            state["direct"] = state["direct"] or (len(parts) > 1 and last in MUTATORS)
            state["callees"].add(last)

    def visit(scope, outer: set[str]) -> None:
        local = outer | _bound_in(scope)
        for node in _own_scope(scope):
            check(node, local)
            if isinstance(node, _SCOPES):
                for part in ([*node.decorator_list, *node.args.defaults, *(d for d in node.args.kw_defaults if d)]
                             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else []):
                    for x in ast.walk(part):       # evaluated in this scope when the nested def runs
                        check(x, local)
                visit(node, local)

    visit(fn, set())
    _ANALYSES[fn] = (state["direct"], frozenset(state["callees"]))
    return _ANALYSES[fn]


def _writers(tree: ast.Module, writers: frozenset) -> list[str]:
    """The keys of a file's functions, methods and calling assignments that may write process-global state; an
    assignment whose value makes a call runs that call at import (C2 of the round-6 review)."""
    out = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and global_writes(n, writers)]
    out += [f"{c.name}.{m.name}" for c in tree.body if isinstance(c, ast.ClassDef) for m in c.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and global_writes(m, writers)]
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and not _no_calls(node):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            own = sorted({n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)})
            if own:
                out.append(",".join(own))
    return sorted(out)


def engine_writers(trees) -> frozenset:
    """The names of every engine function or method that may write process-global state, closed under calls (a
    function calling a writer is a writer): the fixed point over all the engine's files."""
    writers: frozenset = frozenset()
    while True:
        found = frozenset(k.split(".")[-1] for tree in trees for k in _writers(tree, writers) if "," not in k)
        if found <= writers:
            return writers
        writers |= found


def _module_walrus(node) -> list[str]:
    """Names an assignment expression (``x := ...``) binds in module scope when a top-level statement runs: in a def's
    decorators, defaults and annotations, a class's decorators, bases and keywords, or anywhere in another statement,
    lambda and function bodies excepted (they run later, in their own scope)."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        a = node.args
        roots = [*node.decorator_list, *a.defaults, *(d for d in a.kw_defaults if d is not None), node.returns,
                 *(x.annotation for x in [*a.posonlyargs, *a.args, *a.kwonlyargs, a.vararg, a.kwarg] if x is not None)]
    elif isinstance(node, ast.ClassDef):
        roots = [*node.decorator_list, *node.bases, *(k.value for k in node.keywords)]
    else:
        roots = [node]
    found, stack = [], [r for r in roots if r is not None]
    while stack:
        n = stack.pop()
        if isinstance(n, ast.NamedExpr) and isinstance(n.target, ast.Name):
            found.append(n.target.id)
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)) or n in roots:
            stack.extend(ast.iter_child_nodes(n))
    return found


def symbols_of(source: str, writers: frozenset | None = None) -> dict[str, str]:
    """The file's symbols (module doc); ``writers`` are the engine's writer names (``engine_writers``), the file's own
    closure when not given."""
    source = _Source(source)
    tree = ast.parse(source)
    out: dict[str, str] = {}
    bound: set[str] = set()

    def put(key: str, text: str, names=()) -> None:
        if "." not in key or key.startswith("<"):   # a top-level statement (the loop's node), not a method
            names = [*names, *_module_walrus(node)]
        twice = sorted(set(names) & bound) or ([key] if key in out else [])
        if len(set(names)) < len(names):
            twice = sorted({n for n in names if names.count(n) > 1})
        if twice:
            raise SymbolError(f"two top-level symbols bind {twice}")
        bound.update(names)
        out[key] = _digest(text)

    for k, node in enumerate(tree.body):
        text = _segment(source, node) or ""
        if k == 0 and isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) \
                and isinstance(node.value.value, str):
            put("<docstring>", text)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            put(node.name, _with_decorators(source, node), [node.name])
        elif isinstance(node, ast.ClassDef):
            rest = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    put(f"{node.name}.{item.name}", _with_decorators(source, item))
                else:
                    rest.append(_segment(source, item) or "")
            header = ["@" + (_segment(source, d) or "") for d in node.decorator_list]
            put(node.name, "\n".join(header + [node.name] + [ast.unparse(b) for b in node.bases] + rest), [node.name])
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            own = sorted({n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)})
            put(",".join(own) or f"<assign:{_digest(text)[:16]}>", text, own)
        elif isinstance(node, ast.ImportFrom):
            items = ",".join(sorted(f"{a.asname}={a.name}" if a.asname else a.name for a in node.names))
            put(f"<import from {'.' * node.level}{node.module or ''}:names={items}>", text,
                [a.asname or a.name for a in node.names])
        elif isinstance(node, ast.Import):
            own = [a.asname or a.name.split(".")[0] for a in node.names]
            put(f"<import {','.join(sorted(a.asname or a.name for a in node.names))}>", text, own)
        else:
            put(f"<stmt:{_digest(text)[:16]}>", text)
    out[SIDE_EFFECT_FREE] = "true" if side_effect_free(tree) else "false"
    out[GLOBAL_WRITES] = ",".join(_writers(tree, engine_writers([tree]) if writers is None else writers))
    return out


def symbols(engine: pathlib.Path = ENGINE) -> dict[str, dict[str, str]]:
    sources = {p.name: p.read_text(encoding="utf-8") for p in engine_files(engine)}
    writers = engine_writers([ast.parse(text) for text in sources.values()])
    return {name: symbols_of(text, writers) for name, text in sources.items()}


def _bindings(key: str) -> set[tuple[str, str, str]]:
    """(module, imported name, bound name) for each name an ``<import from ...>`` key binds; empty for other keys."""
    match = IMPORT.fullmatch(key)
    if not match:
        return set()
    module = match.group(1) + match.group(2)
    return {(module, item.split("=")[-1], item.split("=")[0]) for item in filter(None, match.group(3).split(","))}


def _top_names(file_symbols: dict[str, str]) -> set[str]:
    names = set()
    for key in file_symbols:
        if IMPORT.fullmatch(key):
            names |= {bound for _, _, bound in _bindings(key)}
        elif not key.startswith("<"):
            names |= set(key.split(".")[0].split(","))
    return names


def _allowed(file: str, symbol: str, base: dict[str, dict[str, str]], new: dict[str, dict[str, str]]) -> bool:
    if symbol in TRAINING_ONLY.get(file, set()):
        return f",{symbol}," not in f",{new.get(file, {}).get(GLOBAL_WRITES, '')},"   # a multi-name key, too
    reviewed = REVIEWED.get(f"{file}:{symbol}")
    if reviewed is not None and not symbol.startswith("<"):   # never a record or import key (brief [O1], [D9])
        return (base.get(file, {}).get(symbol) == reviewed["base"]
                and new.get(file, {}).get(symbol) == reviewed["new"])
    match = IMPORT.fullmatch(symbol)
    if not match:
        return False
    old_file, new_file = base.get(file, {}), new.get(file, {})
    old = set().union(*map(_bindings, old_file))
    now = set().union(*map(_bindings, new_file))
    if symbol not in new_file:                      # removed: every binding it made is still made, unchanged
        return _bindings(symbol) <= now
    source = new.get(f"{match.group(2)}.py")
    if match.group(1) != "." or source is None or source.get(SIDE_EFFECT_FREE) != "true":
        return False
    old_names = _top_names(old_file)
    others = _top_names({k: v for k, v in new_file.items() if k != symbol})
    return all(b in old or (b[2] not in old_names and b[2] not in others and b[2] not in vars(builtins))
               for b in _bindings(symbol))


def certify(base: dict[str, dict[str, str]], new: dict[str, dict[str, str]]) -> dict:
    """Every differing symbol, and whether each is training-only (module doc)."""
    changed, outside = {}, []
    for name in sorted(set(base) | set(new)):
        if name not in base or name not in new:
            changed[name] = ["<whole file added or removed>"]
            outside.append(f"{name}:<whole file>")
            continue
        a, b = base[name], new[name]
        diff = sorted(s for s in set(a) | set(b) if a.get(s) != b.get(s))
        if diff:
            changed[name] = diff
            outside += [f"{name}:{s}" for s in diff if not _allowed(name, s, base, new)]
    return {"changed": changed, "evaluation_path_symbols_changed": outside, "evaluation_path_unchanged": not outside}


def covered(identity_file: str) -> bool:
    """Whether a code-identity file (``safety_selection/X.py``) is in the symbol inventory (the engine's top-level
    files). The reused minimal_safety modules are not: a change in one is never certified."""
    parts = identity_file.split("/")
    return len(parts) == 2 and parts[0] == ENGINE.name and parts[1].endswith(".py")


def missing_training_only(new: dict[str, dict[str, str]]) -> list[str]:
    """TRAINING_ONLY names that the engine does not define (a stale or mistyped allowance)."""
    return sorted(f"{f}:{s}" for f, names in TRAINING_ONLY.items() for s in names if s not in new.get(f, {}))


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
        current = {"symbols": symbols(), "identity": code_identity()}
        missing = missing_training_only(current["symbols"])
        if missing:
            raise SystemExit(f"TRAINING_ONLY names a symbol the engine does not define: {missing}")
        pairs = []
        for spec in argv[2:]:
            paths = [pathlib.Path(p) for p in spec.split(",")]
            base = {"symbols": json.loads(paths[0].read_text()), "identity": json.loads(paths[1].read_text())}
            new = current if len(paths) == 2 else {"symbols": json.loads(paths[2].read_text()),
                                                   "identity": json.loads(paths[3].read_text())}
            out = certify(base["symbols"], new["symbols"])
            if not out["evaluation_path_unchanged"]:
                raise SystemExit(f"{spec}: the evaluation path differs: {out['evaluation_path_symbols_changed']}")
            a, b = base["identity"]["files"], new["identity"]["files"]
            uncovered = sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f) and not covered(f))
            if uncovered:
                raise SystemExit(f"{spec}: changed files outside the symbol inventory: {uncovered}")
            pairs.append({"base_code_sha256": base["identity"]["sha256"], "code_sha256": new["identity"]["sha256"],
                          "changed_files": sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f)),
                          "changed_symbols": out["changed"],
                          "base_symbols_sha256": _digest(json.dumps(base["symbols"], sort_keys=True)),
                          "symbols_sha256": _digest(json.dumps(new["symbols"], sort_keys=True))})
        record = {"kind": "engine evaluation-path equivalence",
                  "rule": "scripts/evaluation_path.py: every top-level symbol of the engine files that differs between "
                          "the two engines is in TRAINING_ONLY (each entry justified there), an import from a "
                          "side-effect-free engine module that shadows no name, or REVIEWED (exact text, pair-scoped); "
                          "a baseline evaluated by the base engine "
                          "may then be paired with a fine-tune of the other (scripts/family_probe_reading.py), together "
                          "with equal evaluation configs and equal pod environments",
                  "training_only": {k: sorted(v) for k, v in TRAINING_ONLY.items()}, "pairs": pairs,
                  "reviewed": REVIEWED}
        pathlib.Path(argv[1]).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
        print(json.dumps([{k: p[k] for k in ("base_code_sha256", "code_sha256", "changed_files")} for p in pairs], indent=1))
        return 0
    raise SystemExit("usage: evaluation_path.py symbols [ENGINE_DIR] | certify BASE_SYMBOLS.json [ENGINE_DIR] | "
                     "certificate OUT.json PAIR [PAIR ...]")


if __name__ == "__main__":
    sys.exit(main())
