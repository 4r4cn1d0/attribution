"""Granite through the lead's backend: the triples path's prompt bytes against the screen's previous builder (commit
e3ce85b) and second_judge_probe.py (the Mac's judge venv and tokenizer, offline), the absence of any prompt, parse,
load or build code in the screen, and the screen's row loop over the lead's judge_triples (the lead's real
GraniteSession with a fake model): order, labels, the retry, stop, resume, one model load per step."""
from __future__ import annotations

import ast
import json
import os
import pathlib
import subprocess

import pytest
from conftest import HERE, TOOL, P, R, FakeGranite, fiction_row, needs_real, sha, write_jsonl
from common import Refusal
import granite_files
import granite_pod
import granite_screen as G

JUDGE_PY = P.ROOT / "tmp/judge-venv/bin/python"
BEFORE_COMMIT, BEFORE_PATH = "e3ce85b", "research/side-fiction/screen-pod/tool/granite_screen.py"
BEFORE_SHA256 = "501eb4a20f2009a878eccbffa5da53291a34973e50c1bf35b832ea3d5267944f"   # the reviewed screen, not launched


def before_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """The screen's own prompt builder before the refactor, from git, pinned by SHA-256."""
    done = subprocess.run(["git", "-C", str(P.W), "show", f"{BEFORE_COMMIT}:{BEFORE_PATH}"], capture_output=True,
                          timeout=60)
    if done.returncode != 0:
        pytest.skip("commit e3ce85b is not reachable from the worktree")
    assert sha(done.stdout) == BEFORE_SHA256
    path = tmp_path / "granite_screen_before.py"
    path.write_bytes(done.stdout)
    return path


def _parity(tmp_path, rows: int) -> dict:
    done = subprocess.run([str(JUDGE_PY), "-I", "-B", str(HERE / "granite_parity_helper.py"), "--tool", str(TOOL),
                           "--probe", str(P.SECOND_JUDGE_PROBE), "--before", str(before_file(tmp_path)),
                           "--rows", str(rows)], capture_output=True, text=True, timeout=1800,
                          env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                               "HOME": os.environ.get("HOME", "/tmp")}, cwd="/")
    assert done.returncode == 0, done.stderr[-2000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


@needs_real
@pytest.mark.skipif(not (JUDGE_PY.is_file() and P.SECOND_JUDGE_PROBE.is_file()),
                    reason="the Mac's judge venv or second_judge_probe.py is absent")
def test_the_triples_path_gives_the_previous_prompt_bytes_with_the_real_tokenizer(tmp_path):
    """BYTE IDENTITY. The real template (transformers 5.18.0, the pinned tokenizer folder) through the pod's path
    (granite_pod.judge_triples -> GraniteSession -> granite_files.granite_input), the screen's own builder before the
    refactor and second_judge_probe.py: 6 synthetic fixtures (one trimmed), 300 real rows of each arm and the gate's
    200 known answers give identical "harm" bytes on all three paths and identical "sexual_content" bytes to the
    previous builder; judge_triples' input_sha256 is the SHA-256 of the text the model received."""
    out = _parity(tmp_path, 300)
    assert out["probe_sha256"] == P.SECOND_JUDGE_PROBE_SHA256 and out["before_sha256"] == BEFORE_SHA256
    assert out["versions"] == {"Jinja2": "3.1.6", "tokenizers": "0.23.2", "transformers": "5.18.0"}
    assert out["tokenizer_matches_pins"] is out["fingerprint_is_macs"] is out["probe_tok_is_lead_tok"] is True
    assert out["tokenizer_loads"] == 1                                    # one session: one tokenizer load
    assert out["init_kwargs_equal"] and out["init_kwargs"] == ["logits_all", "model_path", "n_ctx", "n_gpu_layers",
                                                               "seed", "verbose"]
    assert out["call_kwargs_equal"] and out["label_parse_equal"]
    for case, n in (("fixtures", 6), ("real_rows", 600), ("ka", 200)):
        c = out[case]
        assert c["n"] == n and c["harm_vs_probe"] == c["harm_vs_before"] == c["sexual_vs_before"] == n, case
        assert c["input_sha256_ok"] == c["trimmed_equal"] == c["tokens_equal"] == n, case
    assert out["fixtures"]["trimmed"] >= 1 and out["real_rows"]["trimmed"] == 0 and out["ka_inputs_equal"] == 200


def test_probe_file_is_the_pinned_convention():
    if not P.SECOND_JUDGE_PROBE.is_file():
        pytest.skip("second_judge_probe.py is absent")
    assert sha(P.SECOND_JUDGE_PROBE.read_bytes()) == P.SECOND_JUDGE_PROBE_SHA256
    olmo = P.ROOT / "tmp/family-probe-olmo2-1b/second_judge_probe.py"          # the run that labelled the known answers
    if olmo.is_file():
        assert sha(olmo.read_bytes()) == P.SECOND_JUDGE_PROBE_SHA256


def _code_facts(path: pathlib.Path) -> dict:
    """What a module's code (not its docstrings) calls, imports, passes as keywords and holds as string constants."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                  if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
                  and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    facts = {"calls": set(), "imports": set(), "keywords": set(), "strings": []}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            facts["calls"].add(n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", None))
            facts["keywords"].update(k.arg for k in n.keywords)
        elif isinstance(n, ast.Import):
            facts["imports"].update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            facts["imports"].add(n.module)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings:
            facts["strings"].append(n.value)
    return facts


def test_the_screen_holds_no_granite_prompt_parse_load_or_build_code():
    """ONE backend: no tool module renders a template, parses a score, constructs or resets a model, imports
    llama_cpp or transformers, or passes a guardian_config; screen_run.sh neither installs nor builds
    llama-cpp-python (the lead's pod_run_granite.sh does); the screen's Granite requirement files are gone; the
    Granite calls are the lead's judge_triples."""
    bad = {}
    for path in sorted(TOOL.glob("*.py")):
        f = _code_facts(path)
        hits = sorted({"apply_chat_template", "reset", "Llama", "from_pretrained"} & f["calls"])
        hits += sorted({"llama_cpp", "transformers"} & f["imports"])
        hits += sorted({"guardian_config", "max_tokens", "top_k"} & f["keywords"])
        hits += [s for s in f["strings"] if "<score>" in s or "criteria_id" in s]
        if hits:
            bad[path.name] = hits
    assert bad == {}
    run = "\n".join(x for x in (TOOL / "screen_run.sh").read_text().splitlines() if not x.lstrip().startswith("#"))
    assert not [x for x in ("CMAKE_ARGS=", "llama_cpp_python", "llama-requirements", "--no-binary", "FORCE_CMAKE",
                            "granite-requirements", "nvcc", "apt-get") if x in run]
    assert "bash bundle/gate_b/tool/pod/pod_run_granite.sh" in run and 'VG="${GRANITE_VENV:-/root/granite-venv}"' in run
    assert not (TOOL / "llama-requirements.txt").exists() and not (TOOL / "granite-requirements.txt").exists()
    assert "judge_triples" in _code_facts(TOOL / "granite_screen.py")["calls"]
    assert G.granite_pod is granite_pod and granite_pod.granite_input is granite_files.granite_input


# ------------------------------------------------------------------------------------------------ the row loop

def _rows(tmp_path, n=4):
    path = write_jsonl(tmp_path / "dark.jsonl", [fiction_row("dark", 1, i) for i in range(n)])
    return R.read_rows("dark", path, sha(path.read_bytes()), n)


def _cache(tmp_path, name="g.jsonl"):
    return R.JsonlCache(tmp_path / name, R.check_granite, R.granite_key)


def test_each_row_goes_harm_then_sexual_through_judge_triples_with_one_model_load(tmp_path):
    rows = _rows(tmp_path)
    fake = FakeGranite()
    session, cache, logs = fake.session(), _cache(tmp_path), []
    res = G.screen(session, rows, cache, lambda: False, lambda **k: logs.append(k))
    assert res == {"judged": 8, "cached": 0, "todo": 8, "stopped": False, "calls": 8, "retries": 0}
    assert [(c, h) for c, _, h in fake.seen] == [(c, r.response_sha256) for r in rows for c in P.CRITERIA]
    assert all(u == r.user_sha256 for (_, u, _), r in zip(fake.seen, [r for r in rows for _ in P.CRITERIA]))
    assert (fake.loads, fake.checks, fake.tokenizers) == (1, 1, 1)          # one session: one check, one load
    entries = list(cache.entries.values())
    assert [(e["row_id"], e["criteria"]) for e in entries[:2]] == [("dark-1", "harm"), ("dark-1", "sexual_content")]
    for e in entries:
        assert e["label"] in ("Yes", "No") and e["attempts"] == 1 and e["reason"] is None and len(e["input_sha256"]) == 64
    cache.close()


def test_labels_map_and_an_unparsed_label_gets_one_retry(tmp_path):
    rows = _rows(tmp_path, 3)
    fake = FakeGranite(unparsed_once={rows[0].response_sha256}, unparsed={rows[1].response_sha256},
                       harm={rows[2].response_sha256: "yes"})
    cache = _cache(tmp_path)
    res = G.screen(fake.session(), rows, cache, lambda: False, lambda **k: None)
    assert res["retries"] == 4 and res["calls"] == 10 and res["judged"] == 6        # 2 + 2 retried, then 2 clean
    got = {(e["row_id"], e["criteria"]): e for e in cache.entries.values()}
    assert (got[("dark-1", "harm")]["attempts"], got[("dark-1", "harm")]["reason"]) == (2, None)
    assert got[("dark-2", "harm")]["label"] == "invalid" and got[("dark-2", "harm")]["reason"] == "unparsed"
    assert got[("dark-2", "harm")]["attempts"] == 2 and R.dropped(got[("dark-2", "harm")]["label"])
    assert got[("dark-3", "harm")]["label"] == "Yes" and got[("dark-3", "harm")]["attempts"] == 1
    assert [R.granite_label(x) for x in ("yes", "no", "unparsed")] == ["Yes", "No", "invalid"]
    with pytest.raises(Refusal):
        R.granite_label("maybe")
    cache.close()


def test_stop_resume_and_an_error_ends_the_step(tmp_path):
    rows = _rows(tmp_path)
    stops = {"n": 0}

    def stop():
        stops["n"] += 1
        return stops["n"] > 3
    cache = _cache(tmp_path)
    res = G.screen(FakeGranite().session(), rows, cache, stop, lambda **k: None)
    assert res["stopped"] and 1 <= res["judged"] <= 3
    cache.close()
    again = _cache(tmp_path)
    fake = FakeGranite()
    res = G.screen(fake.session(), rows, again, lambda: False, lambda **k: None)
    assert res["cached"] + res["judged"] == 8 and len(again) == 8 and fake.calls == res["judged"]
    again.close()
    boom = FakeGranite(raise_on={rows[1].response_sha256})
    with pytest.raises(MemoryError):                                       # no row is labelled invalid for an error
        G.screen(boom.session(), rows, _cache(tmp_path, "g3.jsonl"), lambda: False, lambda **k: None)
    assert len(R.JsonlCache(tmp_path / "g3.jsonl", R.check_granite, R.granite_key)) == 2
    assert len(R.selected(rows, 2)) == 2 and len(R.selected(rows, None)) == 4


def test_an_input_over_the_limit_refuses_before_the_model_loads(tmp_path):
    """The lead's precheck (8,160 tokens after the trim, which cuts only the response) refuses the step, naming the
    triple's id, before the model loads: no row is labelled invalid for its length."""
    path = write_jsonl(tmp_path / "long.jsonl", [fiction_row("dark", 1, 0, context="c" * 40000),
                                                 fiction_row("dark", 1, 1)])
    rows = R.read_rows("dark", path, sha(path.read_bytes()), 2)
    fake = FakeGranite()
    with pytest.raises(Refusal, match="dark-1"):                       # the lead's precheck names the triple's id
        G.screen(fake.session(), rows, _cache(tmp_path), lambda: False, lambda **k: None)
    assert fake.loads == 0 and fake.calls == 0
