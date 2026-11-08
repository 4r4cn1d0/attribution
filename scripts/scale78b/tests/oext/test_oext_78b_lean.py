"""The lean command (c0 at 7-8B): the copy scripts/scale78b/lean_eval_job_78b.py (DES E4's copy route) rebuilt from the
1B file by the listed substitutions; run through the wrapper with a family's settings on ENGINEERING FIXTURES (the
engine's synthetic prepared set and tiny policy, the synthetic PHTest bank), its sealed files equal the 1B lean job's
byte for byte and its record differs only in the identity of the file that ran and its settings; the pending branch
refuses; the copy's timer origin precedes the engine's import under the wrapper. None of these numbers is a scientific
result."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("torch")

import b17_support as bs  # noqa: E402
import lean_copy_spec as spec  # noqa: E402
import oext78_fixtures as f  # noqa: E402

w, oe = f.w, f.oe
lej_1b = bs.lej
REPO = Path(w.__file__).resolve().parents[2]
IDENTITY_FIELDS = {"provenance.script", "provenance.script_sha256", "provenance.settings_sha256",
                   "lean_unit.complete_sha256", "training.complete_sha256"}


# ----- the copy ----------------------------------------------------------------------------------------------------


def test_the_copy_is_the_1b_file_rebuilt_by_the_listed_substitutions():
    source = (REPO / spec.SOURCE).read_bytes()
    assert f.s1.sha256_bytes(source) == spec.SOURCE_SHA256              # the 1B file is the frozen one
    rebuilt = spec.rebuild(source.decode("utf-8")).encode("utf-8")
    assert (REPO / spec.COPY).read_bytes() == rebuilt
    assert w.CODE[w.LEAN_MODULE] == f.s1.sha256_bytes(rebuilt)
    assert len(spec.SUBSTITUTIONS) == 5


def test_each_substitution_is_needed_and_the_copy_keeps_every_rule():
    copy_text = (REPO / spec.COPY).read_text(encoding="utf-8")
    source = (REPO / spec.SOURCE).read_text(encoding="utf-8")
    for find, replace in spec.SUBSTITUTIONS:
        assert source.count(find) == 1 and replace in copy_text and find != replace
    assert '"scripts/stage1_s1/settings/oext_eval.json"):' in source and \
        '"scripts/stage1_s1/settings/oext_eval.json"):' not in copy_text
    assert 'pin["path"]) != (oe.OWNER, OEXT_SETTINGS_PATH):' in copy_text
    lej = w.module(w.LEAN_MODULE)
    assert lej.oe is oe and lej.OEXT_SETTINGS_PATH == "scripts/stage1_s1/settings/oext_eval.json"
    assert not lej.SETTINGS_PATH.exists()                  # run alone, the copy finds no settings and refuses
    code, _, err = f.call(lej.main, ["run", "--job", "j", "--prepared", "p", "--recipe", "r", "--out", "o"])
    assert code == 2 and "FileNotFoundError" in err


# ----- a world ---------------------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def prepared(tmp_path_factory):
    return bs.prepared_dirs(tmp_path_factory.mktemp("lean78-prepared"))


def lean_env(base: Path, prepared, branch: str = "128"):
    from types import SimpleNamespace

    prepared_dir, manifest = prepared
    fam = f.Family(base / "fam")
    fam.manifest = manifest
    inp = f.oext_inputs(base / "inputs", fam, branch=branch)
    common = {"lean.overrefusal_bank.status": "oext_pinned", "oext.module_sha256": oe.module_sha256(),
              "oext.settings.sha256": inp.eval_sha, "oext.branch": branch}
    doc78 = bs.settings_doc(**common, **{"oext.settings.path": fam.label("oext_eval"),
                                         "owner": "scripts/scale78b/lean_eval_job_78b.py"})
    lean_path, lean_sha = fam.put("lean_eval_job", doc78)
    doc1b = bs.settings_doc(**common)
    p1b = base / "1b" / "lean_eval_job.json"
    s1b = f.write(p1b, doc1b)
    rec = bs.recipe()
    recipe_path = bs.write_recipe(base / "recipe.json", rec)
    job = base / "job.json"
    bs.write_job(job, prepared_dir, rec)

    def args(out: Path, w1_18: bool = True) -> list[str]:
        out_args = ["run", "--job", str(job), "--prepared", str(prepared_dir), "--recipe", str(recipe_path),
                    "--out", str(out), "--oext-bank", str(inp.bank), "--oext-record", str(inp.record)]
        return out_args + (["--w1-18-record", str(inp.w1_18)] if w1_18 and inp.w1_18 is not None else [])

    return SimpleNamespace(fam=fam, inp=inp, lean_path=lean_path, lean_sha=lean_sha, p1b=p1b, s1b=s1b, args=args,
                           base=base)


@pytest.fixture(scope="module")
def done(tmp_path_factory, prepared):
    """The wrapper's lean run and the 1B lean job's run of the same job (same out path, the first moved aside)."""
    def make():
        env = lean_env(tmp_path_factory.mktemp("lean78"), prepared)
        out = env.base / "out"
        code, _, err = f.wrapper(env.fam, ["lean", "--family", f.FAMILY, *env.args(out)],
                                 loaders=bs.fx.fixture_loaders())
        assert code == 0, err[-400:]
        wrapped = out.rename(env.base / "out-wrapper")
        with w.patched([(lej_1b, "SETTINGS_PATH", env.p1b), (lej_1b, "SETTINGS_SHA256", env.s1b)]):
            code, _, err = f.call(lej_1b.main, env.args(out), loaders=bs.fx.fixture_loaders(),
                                  oext_settings=oe.settings_from_doc(env.inp.eval_doc))
        assert code == 0, err[-400:]
        return env, wrapped, out

    return bs.kept(make)


def _flat(obj, prefix=""):
    if isinstance(obj, dict) and obj:
        return {k: v for key, value in obj.items() for k, v in _flat(value, f"{prefix}{key}.").items()}
    return {prefix[:-1]: obj}


def test_the_sealed_files_are_the_1b_lean_jobs_bytes(done):
    env, wrapped, direct = done
    result = f.compare(wrapped, direct, set())
    sealed = {n: v for n, v in result.items() if n.startswith("lean/sealed/")}
    assert len(sealed) == 9 and set(sealed.values()) == {"bytes"}, sealed
    assert all(v in ("bytes", "parsed") for n, v in result.items() if n.startswith("train/")), result


def test_the_record_differs_only_in_the_identity_of_the_file_that_ran(done):
    env, wrapped, direct = done
    a = _flat(f.strip(json.loads((wrapped / "c0_record.json").read_bytes())))
    b = _flat(f.strip(json.loads((direct / "c0_record.json").read_bytes())))
    assert set(a) == set(b)
    assert {k for k in a if a[k] != b[k]} == IDENTITY_FIELDS
    assert a["provenance.script"] == f.s1.rel(REPO / spec.COPY) and b["provenance.script"] == spec.SOURCE
    assert a["provenance.script_sha256"] == w.CODE[w.LEAN_MODULE] and b["provenance.script_sha256"] == spec.SOURCE_SHA256
    assert (a["provenance.settings_sha256"], b["provenance.settings_sha256"]) == (env.lean_sha, env.s1b)
    assert a["oext.settings_sha256"] == env.inp.eval_sha and a["oext.w1_18_record_sha256"] == env.inp.w1_18_sha256
    job_a = json.loads((wrapped / "lean" / "lean_job.json").read_bytes())
    job_b = json.loads((direct / "lean" / "lean_job.json").read_bytes())
    assert {k for k in job_a if job_a[k] != job_b[k]} == {"settings_sha256"}


def test_the_familys_lean_settings_name_the_file_the_run_read(done):
    env, wrapped, _ = done
    doc = json.loads(env.lean_path.read_bytes())
    assert doc["oext"]["settings"] == {"path": env.fam.label("oext_eval"), "sha256": env.inp.eval_sha}
    with pytest.raises(f.s1.Refusal, match="oext names the O-ext module and its settings file"):
        lej_1b.check_lean_settings(doc)                     # the 1B literal (lean_eval_job.py:229) refuses the label
    lej = w.module(w.LEAN_MODULE)
    with w.patched([(lej, "OEXT_SETTINGS_PATH", env.fam.label("oext_eval"))]):
        assert lej.check_lean_settings(doc) is doc


def test_the_pending_branch_refuses_the_lean_job(tmp_path, prepared):
    env = lean_env(tmp_path, prepared, branch=oe.PENDING)
    code, out, err = f.wrapper(env.fam, ["lean", "--family", f.FAMILY, *env.args(tmp_path / "o", w1_18=False)],
                               loaders=bs.fx.fixture_loaders())
    assert code == 2 and "pending W1-18" in err and not (tmp_path / "o").exists()
    env.fam.waits = [{"pin": "W1_18_BRANCH", "event": "the family's 7-8B W1-18 check", "where": ["families.x.w1_18"],
                      "roles": ["lean_eval_job"]}]
    code, out, err = f.wrapper(env.fam, ["lean", "--family", f.FAMILY, *env.args(tmp_path / "o", w1_18=False)])
    assert code == 2 and "the pin W1_18_BRANCH is null" in err
    assert not any(t in out + err for t in f.fixture_texts())


def test_the_lean_globals_are_restored(done):
    lej = w.module(w.LEAN_MODULE)
    assert lej.SETTINGS_PATH == REPO / "scripts" / "scale78b" / "settings" / "lean_eval_job.json"
    assert lej.SETTINGS_SHA256 == "b0ab19ec28946334e4a033897c1097894fdf5797507f6a516614afc1c2c22acd"
    assert lej.OEXT_SETTINGS_PATH == "scripts/stage1_s1/settings/oext_eval.json"
    assert oe.load_pinned_settings.__name__ == "load_pinned_settings"


def test_under_the_wrapper_the_copys_timer_origin_precedes_the_engine(tmp_path):
    """c0's timer origin is the copy's first statements, before torch and the engine (lean_eval_job.py's docstring):
    the wrapper imports the copy before anything else, so in a fresh interpreter neither torch nor the engine's
    engine module is loaded when the copy starts."""
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import sys, importlib.abc\n"
        f"sys.path.insert(0, {str(REPO)!r})\n"
        "seen = {}\n"
        "class Spy(importlib.abc.MetaPathFinder):\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name == 'scripts.scale78b.lean_eval_job_78b' and not seen:\n"
        "            seen.update(torch='torch' in sys.modules,\n"
        "                        engine='experiments.safety_selection.engine' in sys.modules)\n"
        "        return None\n"
        "sys.meta_path.insert(0, Spy())\n"
        "from scripts.scale78b import oext_78b as w\n"
        "import hashlib\n"
        "idx = sys.argv[2]\n"
        "sha = hashlib.sha256(open(idx, 'rb').read()).hexdigest()\n"
        "code = w.main(['lean', '--family', 'olmo2-7b', '--index', idx, '--index-sha256', sha, 'verify', '--out',\n"
        "               sys.argv[1]])\n"
        "print(seen, code)\n", encoding="utf-8")
    index = f.mk.SETTINGS_DIR / f.mk.index_name("olmo2-7b", "X")
    done_ = subprocess.run([sys.executable, "-B", str(probe), str(tmp_path / "absent"), str(index)], capture_output=True,
                           text=True, timeout=300, cwd=REPO)
    assert "{'torch': False, 'engine': False}" in done_.stdout, (done_.stdout, done_.stderr[-400:])


def test_a_lean_settings_file_naming_the_1b_oext_file_refuses(tmp_path, prepared):
    """GXB O3 for lean (verifier O2): a lean settings file that names the 1B O-ext file while the run reads the
    family's file refuses through the copy's validator; the label comes from the index, never from the file."""
    env = lean_env(tmp_path, prepared)
    doc = json.loads(env.lean_path.read_bytes())
    doc["oext"]["settings"]["path"] = "scripts/stage1_s1/settings/oext_eval.json"
    env.fam.put("lean_eval_job", doc)
    code, out, err = f.wrapper(env.fam, ["lean", "--family", f.FAMILY, *env.args(tmp_path / "o")],
                               loaders=bs.fx.fixture_loaders())
    assert code == 2 and "oext names the O-ext module and its settings file" in err and not (tmp_path / "o").exists()


def test_lean_refuses_the_other_familys_prepared_set_and_a_missing_w1_18_record(tmp_path, prepared):
    env = lean_env(tmp_path, prepared)
    fake = tmp_path / "other-prepared"
    fake.mkdir()
    (fake / "manifest.json").write_bytes(b'{"kind": "other"}')
    env.fam.other_manifest = f.sha(fake / "manifest.json")
    args = env.args(tmp_path / "o")
    args[args.index("--prepared") + 1] = str(fake)
    code, _, err = f.wrapper(env.fam, ["lean", "--family", f.FAMILY, *args])
    assert code == 2 and "(the other family's manifest)" in err and f.sha(fake / "manifest.json") in err
    code, _, err = f.wrapper(env.fam, ["lean", "--family", f.FAMILY, *env.args(tmp_path / "o", w1_18=False)])
    assert code == 2 and f"pin W1-18's record {env.inp.w1_18_sha256} (branch 128): --w1-18-record is needed" in err
    assert not (tmp_path / "o").exists()


def test_the_lean_globals_are_restored_when_the_copy_raises(tmp_path, prepared, monkeypatch):
    """Verifier O4: an exception inside the copy's main (a crash in its plan) restores every global."""
    env = lean_env(tmp_path, prepared)
    lej = w.module(w.LEAN_MODULE)
    before = (lej.SETTINGS_PATH, lej.SETTINGS_SHA256, lej.OEXT_SETTINGS_PATH, oe.load_pinned_settings,
              oe.w1_18.SETTINGS_PATH, oe.w1_18.SETTINGS_SHA256)

    def crash(*a, **k):
        raise RuntimeError("fixture: the plan crashes")

    monkeypatch.setattr(lej, "prepare_c0_job", crash)
    with pytest.raises(RuntimeError, match="fixture: the plan crashes"):
        w.main(["lean", *env.fam.leading(), *env.args(tmp_path / "o")], loaders=bs.fx.fixture_loaders())
    assert (lej.SETTINGS_PATH, lej.SETTINGS_SHA256, lej.OEXT_SETTINGS_PATH, oe.load_pinned_settings,
            oe.w1_18.SETTINGS_PATH, oe.w1_18.SETTINGS_SHA256) == before
