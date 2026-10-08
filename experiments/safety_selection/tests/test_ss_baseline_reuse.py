"""Baseline reuse across engine identities (GI III rounds 5 and 6): the engine's evaluation path is unchanged from both
pinned bases (04eb83a3 at 42eb258, 55253874 at 8c026ee), symbol by symbol (scripts/evaluation_path.py against the
pinned base inventories), and the pinned evaluation-equivalence certificate describes exactly this engine. A later
engine change fails here until it is certified again."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest

from experiments.safety_selection.common import code_identity

ROOT = Path(__file__).resolve().parents[3]
CONFIGS = ROOT / "experiments/safety_selection/configs"
CERTIFICATE = CONFIGS / "evaluation-equivalence-round6-20261008.json"
BASES = {"04eb83a3fca6fc77ae81d8975d52ae642f7efafb774759e01ca88b6c3fd51408": "04eb83a3",
         "552538748acec1a8ffd1ee976b9eb3c3fdfe9ca01b8148ee8810291409357441": "55253874"}


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TOOL = load("evaluation_path", ROOT / "scripts" / "evaluation_path.py")


def ep():
    return TOOL


def base(short: str) -> tuple[dict, dict]:
    return (json.loads((CONFIGS / f"evaluation-path-symbols-v2-{short}.json").read_text()),
            json.loads((CONFIGS / f"engine-identity-{short}.json").read_text()))


def digest(symbols: dict) -> str:
    return hashlib.sha256(json.dumps(symbols, sort_keys=True).encode("utf-8")).hexdigest()


def differ(a: dict, b: dict) -> list[str]:
    return sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f))


def test_the_engine_certifies_against_both_pinned_bases_and_the_certificate_is_this_engines():
    tool, now = ep(), code_identity()
    current = tool.symbols()
    assert tool.missing_training_only(current) == []
    certificate = json.loads(CERTIFICATE.read_text())
    pairs = {(e["base_code_sha256"], e["code_sha256"]): e for e in certificate["pairs"]}
    assert set(pairs) == {(b, now["sha256"]) for b in BASES} | {tuple(BASES)}
    for sha, short in BASES.items():
        symbols, identity = base(short)
        assert identity["sha256"] == sha
        out = tool.certify(symbols, current)
        assert out["evaluation_path_unchanged"], (short, out["evaluation_path_symbols_changed"])
        entry = pairs[(sha, now["sha256"])]
        assert entry["changed_files"] == differ(identity["files"], now["files"])
        assert entry["changed_symbols"] == out["changed"]
        assert (entry["base_symbols_sha256"], entry["symbols_sha256"]) == (digest(symbols), digest(current))
    (old, old_identity), (new, new_identity) = base("04eb83a3"), base("55253874")
    history = tool.certify(old, new)                # the 04eb83a3 -> 55253874 pair stays valid under the round-6 rule
    assert history["evaluation_path_unchanged"], history["evaluation_path_symbols_changed"]
    entry = pairs[tuple(BASES)]
    assert entry["changed_files"] == differ(old_identity["files"], new_identity["files"])
    assert (entry["changed_symbols"], entry["symbols_sha256"]) == (history["changed"], digest(new))
    assert certificate["training_only"] == {k: sorted(v) for k, v in tool.TRAINING_ONLY.items()}
    reading = load("family_probe_reading", ROOT / "scripts" / "family_probe_reading.py")
    assert reading.CERTIFICATE == CERTIFICATE
    assert reading.CERTIFICATE_SHA256 == hashlib.sha256(CERTIFICATE.read_bytes()).hexdigest()


def test_no_engine_or_loader_star_imports_the_modules_whose_all_lists_are_training_only():
    star = re.compile(r"from\s+\S*(engine|attribution)\s+import\s+\*")
    users = [p for d in ("experiments", "scripts", "runkit") for p in (ROOT / d).rglob("*.py")
             if star.search(p.read_text(encoding="utf-8", errors="replace"))]
    assert users == []


def engine(**files: str) -> dict:
    return {name.replace("_py", ".py"): ep().symbols_of(text) for name, text in files.items()}


def outside(base_files: dict, new_files: dict) -> list[str]:
    return ep().certify(engine(**base_files), engine(**new_files))["evaluation_path_symbols_changed"]


def test_the_symbol_inventory_flags_an_evaluation_change_and_allows_a_training_one():
    base = {"engine_py": "def greedy_generate():\n    return 1\n\ndef train_step():\n    return 1\n",
            "attribution_py": "ROW_WEIGHTING = 1\nX = 1\n"}
    training = {"engine_py": "def greedy_generate():\n    return 1\n\ndef train_step():\n    return 2\n",
                "attribution_py": "ROW_WEIGHTING = 2\nX = 1\n"}
    assert outside(base, base) == [] and outside(base, training) == []
    evaluation = {**training, "engine_py": "def greedy_generate():\n    return 3\n\ndef train_step():\n    return 2\n"}
    assert outside(base, evaluation) == ["engine.py:greedy_generate"]
    assert outside(base, {**training, "scoring_py": "Y = 1\n"}) == ["scoring.py:<whole file>"]
    assert outside(base, {**training, "attribution_py": "ROW_WEIGHTING = 2\nX = 2\n"}) == ["attribution.py:X"]
    methods = {"engine_py": "class M:\n    def f(self):\n        return 1\n\n    def g(self):\n        return 1\n"}
    changed = {"engine_py": methods["engine_py"].replace("return 1\n\n", "return 2\n\n")}
    assert outside(methods, changed) == ["engine.py:M.f"]


def test_a_decorator_change_is_a_symbol_change():
    plain = {"engine_py": "import functools\n\ndef greedy_generate():\n    return 1\n"}
    cached = {"engine_py": "import functools\n\n@functools.lru_cache\ndef greedy_generate():\n    return 1\n"}
    assert outside(plain, cached) == ["engine.py:greedy_generate"]
    method = {"engine_py": "class M:\n    def f(self):\n        return 1\n"}
    wrapped = {"engine_py": "class M:\n    @staticmethod\n    def f(self):\n        return 1\n"}
    assert outside(method, wrapped) == ["engine.py:M.f"]
    assert ep().symbols_of(cached["engine_py"])["<side_effect_free>"] == "true"
    called = "import functools\n\n@functools.lru_cache(maxsize=1)\ndef greedy_generate():\n    return 1\n"
    assert ep().symbols_of(called)["<side_effect_free>"] == "false"


@pytest.mark.parametrize("source", [
    "def f():\n    return 1\n\ndef f():\n    return 2\n",                      # a redefinition hides the first
    "def f():\n    return 1\n\nf = 2\n",
    "from .a import f\n\ndef f():\n    return 1\n",
    "from .a import g as f\nfrom .b import f\n",
    "import os\nos = 1\n",
    "class C:\n    X = 1\n\nC = None\n",
    "a, b = 1, 2\nb = 3\n",
    "class C:\n    def g(self):\n        return 1\n    def g(self):\n        return 2\n",
])
def test_two_top_level_symbols_with_one_name_refuse(source):
    with pytest.raises(ep().SymbolError):
        ep().symbols_of(source)


SIDE_EFFECT_FREE = "def interval_rates():\n    return 1\n\ndef other():\n    return 2\n\nX = 1\n"


def test_an_import_from_a_side_effect_free_module_is_allowed_only_when_it_binds_a_new_name():
    base = {"runner_py": "from .attribution import X\n\ndef evaluate():\n    return X\n",
            "attribution_py": SIDE_EFFECT_FREE}
    regrouped = {**base, "runner_py": "from .attribution import X, interval_rates\n\ndef evaluate():\n    return X\n"}
    assert outside(base, regrouped) == []                                   # X is still attribution.X; the new name is fresh
    shadow = {**base, "runner_py": "from .attribution import X\nfrom .attribution import other as evaluate\n\n"
                                   "def evaluate():\n    return X\n"}
    with pytest.raises(ep().SymbolError):                                   # a same-name import is refused outright
        engine(**shadow)
    rebound = {**base, "runner_py": "from .attribution import other as X\n\ndef evaluate():\n    return X\n"}
    assert outside(base, rebound)                                           # X now names another object
    moved = {**base, "runner_py": "from .config import X\n\ndef evaluate():\n    return X\n", "config_py": "X = 2\n"}
    base_with_config = {**base, "config_py": "X = 2\n"}
    assert outside(base_with_config, moved)                                 # X now comes from another module
    dropped = {**base, "runner_py": "def evaluate():\n    return X\n"}
    assert outside(base, dropped) == ["runner.py:<import from .attribution:names=X>"]   # X no longer bound
    previously_local = {"runner_py": "interval_rates = None\n\ndef evaluate():\n    return 1\n",
                        "attribution_py": SIDE_EFFECT_FREE}
    assert outside(previously_local, {**previously_local, "runner_py": "from .attribution import interval_rates\n\n"
                                                                     "def evaluate():\n    return 1\n"})
    training = {"engine_py": "def train_step():\n    return 1\n", "attribution_py": SIDE_EFFECT_FREE}
    renamed = {**training, "engine_py": "from .attribution import interval_rates as train_step\n"}
    assert outside(training, renamed) == ["engine.py:<import from .attribution:names=train_step=interval_rates>"]


def test_an_import_from_a_module_with_top_level_effects_or_outside_the_engine_is_refused():
    effects = "import os\n\ndef interval_rates():\n    return 1\n\nos.environ.setdefault('A', '1')\n"
    base = {"runner_py": "def evaluate():\n    return 1\n", "attribution_py": effects}
    added = {**base, "runner_py": "from .attribution import interval_rates\n\ndef evaluate():\n    return 1\n"}
    assert outside(base, added) == ["runner.py:<import from .attribution:names=interval_rates>"]
    clean = {"runner_py": "def evaluate():\n    return 1\n"}
    assert outside(clean, {"runner_py": "from os import path\n\ndef evaluate():\n    return 1\n"})
    assert outside(clean, {"runner_py": "import os\n\ndef evaluate():\n    return 1\n"})


def test_a_stale_training_only_name_is_reported(monkeypatch):
    tool = ep()
    monkeypatch.setitem(tool.TRAINING_ONLY, "engine.py", tool.TRAINING_ONLY["engine.py"] | {"no_such_function"})
    assert tool.missing_training_only(tool.symbols()) == ["engine.py:no_such_function"]


def test_a_changed_training_only_function_that_writes_global_state_is_refused():
    """Round 6 review: a training function runs in the evaluation's process, so a global write would reach evaluation."""
    base = {"engine_py": "import torch\n\ndef train_step(x):\n    return x\n"}
    for body in ("    torch.backends.cuda.matmul.allow_tf32 = True\n    return x\n",
                 "    torch.use_deterministic_algorithms(False)\n    return x\n",
                 "    torch.backends.cuda.enable_flash_sdp(False)\n    return x\n",
                 "    import os\n    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ''\n    return x\n",
                 "    global LIMIT\n    LIMIT = 1\n    return x\n",
                 "    setattr(torch, 'flag', 1)\n    return x\n"):
        assert outside(base, {"engine_py": "import torch\n\ndef train_step(x):\n" + body}) == ["engine.py:<global_writes>",
                                                                                              "engine.py:train_step"], body
    local = {"engine_py": "import torch\n\ndef train_step(x):\n    y = {}\n    y['a'] = x\n    x.lr = 2\n    return y\n"}
    assert outside(base, local) == []                    # writes to locals and to a passed object are not detected
    assert TOOL.symbols()["engine.py"][TOOL.GLOBAL_WRITES].split(",") == ["load_state", "lora_parameters",
                                                                           "preserved_rng", "restore_rng"]


@pytest.mark.parametrize("body", [
    "    for torch.backends.cuda.matmul.allow_tf32 in (True,):\n        pass\n",              # a loop target
    "    import contextlib\n    with contextlib.nullcontext(True) as torch.backends.cudnn.benchmark:\n        pass\n",
    "    (_a, (torch.backends.cudnn.benchmark, _b)) = (1, (True, 2))\n",                  # nested unpacking
    "    torch._C._set_cublas_allow_tf32(True)\n",                                          # widened prefixes
    "    torch.seed()\n",
    "    import sys\n    sys.path.append('x')\n",
    "    import numpy as np\n    np.seterr(all='ignore')\n",
    "    LIMITS.update(a=1)\n",                                                            # a global's mutating method
    "    helper()\n",                                                                     # a writer, transitively
    "    en.restore_rng('cuda', [], None)\n",                                              # by its last name
    "    en.load_state('f', x, None, 'cuda')\n",                                           # its RNG restore is on
    "    en.load_state('f', x, None, 'cuda', restore_rng_state=True)\n",                  # on, explicitly
])
def test_each_form_of_a_global_write_in_a_training_only_function_is_refused(body):
    head = "import torch\nfrom . import engine as en\nLIMITS = {}\n\ndef helper():\n    torch.manual_seed(0)\n\n"
    base = {"engine_py": head + "def train_step(x):\n    return x\n"}
    new = {"engine_py": head + "def train_step(x):\n" + body + "    return x\n"}
    writers = TOOL.engine_writers([TOOL.ast.parse(new["engine_py"])]) | {"restore_rng", "load_state"}
    out = TOOL.certify(engine(**base), {"engine.py": TOOL.symbols_of(new["engine_py"], writers)})
    assert "engine.py:train_step" in out["evaluation_path_symbols_changed"], body


@pytest.mark.parametrize("body", [
    "    state = torch.cuda.get_rng_state_all()\n    import random\n    random.getstate()\n",  # read-only calls
    "    with en.preserved_rng('cuda'):\n        pass\n",                                   # net-neutral helper
    "    en.load_state('f', x, None, 'cuda', restore_rng_state=False)\n",                  # its RNG restore is off
    "    rows = []\n    rows.append(x)\n    x.lr = 1\n",                                     # locals, a passed object
])
def test_reads_neutral_helpers_and_local_writes_are_not_global_writes(body):
    head = "import torch\nfrom . import engine as en\n\n"
    base = {"engine_py": head + "def train_step(x):\n    return x\n"}
    new = {"engine_py": head + "def train_step(x):\n" + body + "    return x\n"}
    writers = frozenset({"restore_rng", "load_state", "preserved_rng"})
    out = TOOL.certify(engine(**base), {"engine.py": TOOL.symbols_of(new["engine_py"], writers)})
    assert out["evaluation_path_unchanged"], (body, out["evaluation_path_symbols_changed"])


def test_writers_are_closed_under_calls_across_the_engines_files(tmp_path):
    (tmp_path / "engine.py").write_text("import torch\n\ndef restore(x):\n    torch.set_rng_state(x)\n\n"
                                        "def outer(x):\n    restore(x)\n")
    (tmp_path / "runner.py").write_text("from . import engine as en\n\ndef _train_segment(x):\n    en.outer(x)\n")
    inventory = TOOL.symbols(tmp_path)
    assert inventory["engine.py"][TOOL.GLOBAL_WRITES] == "outer,restore"
    assert inventory["runner.py"][TOOL.GLOBAL_WRITES] == "_train_segment"


def test_a_changed_training_only_assignment_that_makes_a_call_is_refused():
    base = {"engine_py": "import torch\n\nSCHEDULES = ('constant', 'warmup_cosine')\n"}
    called = {"engine_py": "import torch\n\nSCHEDULES = (torch.set_float32_matmul_precision('medium'), "
                           "('constant', 'warmup_cosine'))[1]\n"}
    plain = {"engine_py": "import torch\n\nSCHEDULES = ('constant', 'warmup_cosine', 'warmup_constant')\n"}
    assert "engine.py:SCHEDULES" in outside(base, called) and outside(base, plain) == []


def test_an_import_that_binds_a_builtins_name_is_refused():
    base = {"runner_py": "def arc(scores):\n    return max(scores)\n", "scoring_py": "def fmean(x):\n    return 1\n"}
    shadow = {**base, "runner_py": "from .scoring import fmean as max\n\ndef arc(scores):\n    return max(scores)\n"}
    assert outside(base, shadow) == ["runner.py:<import from .scoring:names=max=fmean>"]


def test_a_change_outside_the_symbol_inventory_is_never_certified(tmp_path):
    """Round 6 review: the reused minimal_safety modules are in the code identity but not in the inventory."""
    now = code_identity()
    symbols, identity = tmp_path / "symbols.json", tmp_path / "identity.json"
    symbols.write_text(json.dumps(TOOL.symbols()))
    identity.write_text(json.dumps({"sha256": "0" * 64, "files": {**now["files"], "minimal_safety/model.py": "0" * 64}}))
    with pytest.raises(SystemExit, match=r"outside the symbol inventory: \['minimal_safety/model.py'\]"):
        TOOL.main(["certificate", str(tmp_path / "out.json"), f"{symbols},{identity}"])
    assert not (tmp_path / "out.json").exists()
    assert [TOOL.covered(f) for f in ("safety_selection/runner.py", "minimal_safety/model.py", "safety_selection/x/y.py")] \
        == [True, False, False]


def test_the_cached_source_segments_equal_the_standard_librarys():
    texts = [p.read_text(encoding="utf-8") for p in TOOL.engine_files(TOOL.ENGINE)]
    texts.append("x = 'é'  # crlf\r\ny = (1,\r\n     2)\rz = 3\n\fw = 'ü' + 'ß'")
    for text in texts:                         # every node symbols_of cuts: top-level, class-level and decorators
        source, tree = TOOL._Source(text), TOOL.ast.parse(text)
        nodes = [*tree.body, *(i for n in tree.body if isinstance(n, TOOL.ast.ClassDef) for i in n.body)]
        nodes += [d for n in nodes for d in getattr(n, "decorator_list", [])]
        for node in nodes:
            assert source.segment(node) == TOOL.ast.get_source_segment(text, node)
    tiny = "x = 'é'  # crlf\r\ny = (1,\r\n     2)\rz = 3\n\fw = 'ü' + 'ß'"
    for node in TOOL.ast.walk(TOOL.ast.parse(tiny)):                       # every node of a small mixed-ending text
        assert TOOL._Source(tiny).segment(node) == TOOL.ast.get_source_segment(tiny, node)


def _train_step_refused(body: str, head: str = "import torch\nimport sys\nimport logging\nLIMITS = {'a': []}\n\n") -> bool:
    base = {"engine_py": head + "def train_step(x):\n    return x\n"}
    out = TOOL.certify(engine(**base), engine(engine_py=head + "def train_step(x):\n" + body + "    return x\n"))
    return "engine.py:train_step" in out["evaluation_path_symbols_changed"]


@pytest.mark.parametrize("body", [
    "    LIMITS['a'].append(1)\n",                                                      # through an item
    "    torch.cuda.default_generators[0].manual_seed(0)\n",
    "    sys.modules['random'].seed(0)\n",
    "    logging.getLogger('transformers').setLevel(50)\n",                             # through a call
    "    getattr(torch, 'use_deterministic_algorithms')(False)\n",
    "    ys = [torch for torch in (1, 2)]\n    torch.manual_seed(0)\n",                     # a comprehension name
    "    def inner(torch):\n        return torch\n    torch.manual_seed(0)\n",               # a nested def's argument
    "    ys = [LIMITS for LIMITS in ([],)]\n    LIMITS.update(a=1)\n",                       # shadowed only in there
    "    ys = [LIMITS for LIMITS in ([],)]\n    LIMITS['a'] = 1\n",
])
def test_round_3_global_write_forms_are_refused(body):
    assert _train_step_refused(body), body


@pytest.mark.parametrize("body", [
    "    rows = [[] for _ in range(2)]\n    [r.append(1) for r in rows]\n",                 # comprehension locals
    "    def inner():\n        tokens = [0]\n        tokens[0] = 1\n    inner()\n",           # a nested def's locals
    "    out = {'a': []}\n    out['a'].append(1)\n",                                       # a local through an item
])
def test_nested_scope_locals_are_not_global_writes(body):
    assert not _train_step_refused(body), body


@pytest.mark.parametrize("source", [
    "TOKEN_ROWS = '.lora_A.'\nSCHEDULES = ('constant', (TOKEN_ROWS := '.x.'))[:1]\n",       # rebinds at import
    "TOKEN_ROWS = '.lora_A.'\n\ndef train_step(w=(1, (TOKEN_ROWS := '.x.'))[0]):\n    return w\n",
])
def test_a_walrus_that_rebinds_a_module_name_at_import_refuses(source):
    with pytest.raises(TOOL.SymbolError):
        TOOL.symbols_of(source)


def test_a_multi_name_training_only_assignment_that_makes_a_call_is_refused():
    base = {"engine_py": "import torch\n\nEXAMPLE_MEAN, TOKEN_MEAN = 'example_mean', 'token_mean'\n"}
    called = {"engine_py": "import torch\n\nEXAMPLE_MEAN, TOKEN_MEAN = 'example_mean', str(torch.seed())\n"}
    assert "engine.py:EXAMPLE_MEAN,TOKEN_MEAN" in outside(base, called)
