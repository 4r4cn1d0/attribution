"""The ported judges keep the pins and rules of the probe-kit originals (syntax-tree comparisons; nothing imported
from the originals, no model). Skips when the originals are not on this machine."""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
MODULES = HERE.parent
sys.path.insert(0, str(MODULES))
from common import BANK_KIND, GRANITE, HARMBENCH, ROOT  # noqa: E402

KIT = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp/family-probe-olmo2-1b")
HB_ORIG, GR_ORIG = KIT / "harmbench_judge.py", KIT / "second_judge_probe.py"
VERBATIM = ("load_template", "_varint", "_fields", "_SpmModel", "load_tokenizer", "clip_generation", "load_judge")


def tree(path: pathlib.Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def defs(mod: ast.Module) -> dict:
    return {n.name: n for n in ast.walk(mod) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


def assigns(mod: ast.Module) -> dict:
    out = {}
    for n in mod.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            out[n.targets[0].id] = n.value
    return out


def named_assigns(fn) -> dict:
    out = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign) and len(n.targets) == 1:
            out.setdefault(ast.dump(n.targets[0]), []).append(ast.dump(n.value))
    return out


def calls(fn, attr: str) -> list:
    out = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            f = n.func
            name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
            if name == attr:
                out.append(ast.dump(ast.Call(func=ast.Name(id="_"), args=n.args, keywords=n.keywords)))
    return out


@pytest.mark.skipif(not HB_ORIG.exists(), reason="original HarmBench script not present")
def test_harmbench_port_keeps_pins_and_rules():
    orig, port = tree(HB_ORIG), tree(MODULES / "harmbench_files.py")
    od, pd = defs(orig), defs(port)
    for name in VERBATIM:
        assert ast.dump(od[name]) == ast.dump(pd[name]), name
    oa, pa = assigns(orig), assigns(port)
    for name in ("TEMPLATE_SHA256", "TOKENIZER_MODEL_SHA256", "TINY_TOKENIZER_DIR", "NUM_TOKENS", "MAX_INPUT_TOKENS",
                 "SNAPSHOT"):
        assert ast.dump(oa[name]) == ast.dump(pa[name]), name
    assert ast.literal_eval(oa["REVISION"]) == HARMBENCH["revision"] and ast.literal_eval(oa["REPO"]) == HARMBENCH["name"]
    # the one-token label rule and the forward pass
    o_items, p_judge = od["judge_items"], pd["harmbench_judge"]
    o_label = named_assigns(o_items)[ast.dump(ast.Name(id="label", ctx=ast.Store()))][0]
    p_rule = next(n.value for n in ast.walk(pd["label_from_token"]) if isinstance(n, ast.Return))
    assert o_label == ast.dump(p_rule)
    oa_i, pa_j = named_assigns(o_items), named_assigns(p_judge)
    for var in ("out", "last", "finite", "tid", "p"):
        key = ast.dump(ast.Name(id=var, ctx=ast.Store()))
        assert oa_i[key] == pa_j[key], var
    assert calls(o_items, "empty_cache") == calls(p_judge, "empty_cache")
    # bank: kind "harm", prompt_id -> prompt
    assert "harm" in ast.dump(od["bank_prompts"]) and ast.dump(oa["MAX_INPUT_TOKENS"]) == ast.dump(ast.Constant(2048))


class _CriterionAsDefault(ast.NodeTransformer):
    """granite_files' criteria_id (a parameter since 9 Oct 2026, default "harm") read as its default."""

    def visit_Name(self, node):
        if node.id == "criteria_id" and isinstance(node.ctx, ast.Load):
            return ast.copy_location(ast.Constant("harm"), node)
        return node


@pytest.mark.skipif(not GR_ORIG.exists(), reason="original Granite script not present")
def test_granite_port_keeps_pins_and_rules():
    orig, port = tree(GR_ORIG), tree(MODULES / "granite_files.py")
    og = defs(orig)["granite_judge"]
    # the criterion is a parameter whose default is the original's "harm"; the comparisons read it as that default
    p0 = defs(port)
    for name in ("granite_input", "granite_precheck"):
        assert p0[name].args.args[-1].arg == "criteria_id" and ast.literal_eval(p0[name].args.defaults[-1]) == "harm"
    kw = p0["granite_judge"].args
    assert kw.kwonlyargs[-1].arg == "criteria_id" and ast.literal_eval(kw.kw_defaults[-1]) == "harm"
    port = _CriterionAsDefault().visit(port)
    pdefs = defs(port)
    # The port splits the original's granite_judge into the template-and-trimming helper (used by the judge and by the
    # pre-load token check), the two loaders and the judge itself; together they must make the same calls.
    pg = ast.Module(body=[pdefs[n] for n in ("granite_input", "granite_judge", "load_granite_tokenizer",
                                             "load_granite_model")], type_ignores=[])
    for attr in ("Llama", "llm", "apply_chat_template", "from_pretrained"):
        assert calls(og, attr) == calls(pg, attr), attr
    assert calls(pdefs["granite_judge"], "granite_input") and calls(pdefs["granite_precheck"], "granite_input")
    body = pdefs["granite_judge"].body                                    # the token check runs before the model loads

    def first(pred):
        return next(i for i, st in enumerate(body) if any(pred(n) for n in ast.walk(st)))
    i_check = first(lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "granite_precheck")
    i_llm = first(lambda n: isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "llm")
    assert i_check < i_llm
    oa, pa = named_assigns(og), named_assigns(pg)
    for target in ("messages", "trimmed", "out"):
        key = ast.dump(ast.Name(id=target, ctx=ast.Store()))
        assert set(oa[key]) == set(pa[key]), target
    trim = [k for k in oa if "content" in k]
    assert trim and oa[trim[0]] == pa[trim[0]]                                   # answer[: max(1000, len*7000/n)]
    o_if = [n for n in ast.walk(og) if isinstance(n, ast.If)][0].test
    p_if = [n for n in ast.walk(pg) if isinstance(n, ast.If)][0].test
    assert ast.dump(o_if.comparators[0]) == ast.dump(p_if.comparators[0]) == ast.dump(ast.Constant(8000))
    o_scores = [n for n in ast.walk(og) if isinstance(n, ast.Assign) and "scores" in ast.dump(n.targets[0])]
    p_parse = defs(port)["parse_score"]
    p_scores = [n for n in ast.walk(p_parse) if isinstance(n, ast.Assign) and "scores" in ast.dump(n.targets[0])]
    assert ast.dump(o_scores[0].value) == ast.dump(p_scores[0].value)               # re.findall(<score>...)
    o_ret = [n for n in ast.walk(og) if isinstance(n, ast.Return) and isinstance(n.value, ast.Tuple)][0].value.elts[0]
    p_lab = [n for n in ast.walk(p_parse) if isinstance(n, ast.Assign) and "label" in ast.dump(n.targets[0])][0].value
    assert ast.dump(o_ret) == ast.dump(p_lab)                                      # last score, strip, lower
    oc, pc = assigns(orig), assigns(port)
    for name in ("MODELS", "GGUF", "TOK"):
        assert ast.dump(oc[name]) == ast.dump(pc[name]), name
    assert ast.literal_eval(oc["KIND"]) == BANK_KIND and GR_ORIG.resolve().parents[2] == ROOT
    assert "granite-guardian-3.3-8b" in GRANITE["name"]
    # the bank reader: prompt_id -> prompt of the dev bank's harm rows, after the manifest comparison
    ob, cb = defs(orig)["bank_prompts"], defs(tree(MODULES / "common.py"))["bank_prompts"]
    key = "Subscript(value=Name(id='prompts'"
    o_set = [v for k, vs in named_assigns(ob).items() if k.startswith(key) for v in vs]
    c_set = [v for k, vs in named_assigns(cb).items() if k.startswith(key) for v in vs]
    assert o_set == c_set and len(o_set) == 1
    o_cmp = [n for n in ast.walk(ob) if isinstance(n, ast.Compare) and isinstance(n.ops[0], ast.NotEq)][0]
    c_cmp = [n for n in ast.walk(cb) if isinstance(n, ast.Compare) and isinstance(n.ops[0], ast.NotEq)][0]
    assert ast.dump(o_cmp.left).count("strip") == ast.dump(c_cmp.left).count("strip") == 1
    assert "manifest.sha256" in ast.dump(o_cmp.left) and "manifest.sha256" in ast.dump(c_cmp.left)
