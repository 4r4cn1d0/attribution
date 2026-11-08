"""Re-verifier's own cascade (R1 Track O fix round; not the builder's cascade_fix.py nor the first verifier's).

For every pin fill, on disk, through the maker's own CLI (main) with --pins P --settings-dir D (one fixed D, so the
path labels are the same in the base and the filled run):
  - which derived files change (by name),
  - which of the four kit forms change (the maker's --oext-78b F / --oext-78b-y F prints),
  - that the wrapper file's bytes are unchanged and that it holds no 64-hex literal outside CODE,
  - that the wrapper's check accepts every family/engine index in D (exit 0) after the fill, with a W1-18 record
    where the fill pins one.
Then the fills in T-O2's order, cumulative, to show each family's X and Y forms stop changing after their last fill.
Usage: PY -B rv_cascade.py WS WORKDIR
"""
import contextlib
import copy
import hashlib
import io
import json
import re
import shutil
import sys
from pathlib import Path

WS, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(WS))
from scripts.scale78b import make_oext_settings_78b as mk  # noqa: E402
from scripts.scale78b import oext_78b as w  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402

assert Path(mk.__file__).resolve().is_relative_to(WS) and Path(w.__file__).resolve().is_relative_to(WS)
FAMS = ("olmo2-7b", "llama31-8b")
D = WORK / "settings"
WRAPPER = WS / "scripts/scale78b/oext_78b.py"
wrapper_sha0 = hashlib.sha256(WRAPPER.read_bytes()).hexdigest()

# the wrapper holds no index hash: every 64-hex literal in its text is one of CODE's values
hexes = set(re.findall(r"[0-9a-f]{64}", WRAPPER.read_text()))
assert hexes <= set(w.CODE.values()), sorted(hexes - set(w.CODE.values()))


def cfg(name):
    rec = load_recipe(WS / "experiments/safety_selection/configs" / f"{name}.json")
    return {"name": name, "config_sha256": config_sha256(rec)}


def call(fn, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(argv)
    return code, out.getvalue(), err.getvalue()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def record_for(family, folder, passed=True):
    """A text-free W1-18-shaped record made under D's W1-18 settings of the family (independent of the builder's)."""
    lim = json.loads((D / f"limits_overrefusal_checks__{family}.json").read_bytes())
    doc = {"kind": "stage1 over-refusal checks", "version": 1,
           "units": {n: {"truncation": {"cap_tokens": lim["truncation"]["cap_tokens"]}} for n in lim["units"]},
           "truncation_check": {"pass": passed},
           "provenance": {"settings_sha256": sha(D / f"limits_overrefusal_checks__{family}.json")}}
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"rec-{family}-{'pass' if passed else 'fail'}.json"
    path.write_bytes(json.dumps(doc, sort_keys=True).encode())
    return path, sha(path)


def state(pins, records):
    """Write pins to WORK/pins.json, run the maker into D, return (file hashes, forms, check exits)."""
    if D.exists():
        shutil.rmtree(D)
    p = WORK / "pins.json"
    p.write_bytes(mk.dumps(pins))
    code, out, err = call(mk.main, ["--pins", str(p), "--settings-dir", str(D)])
    assert code == 0, err
    files = {q.name: sha(q) for q in sorted(D.iterdir())}
    forms = {}
    for fam in FAMS:
        for flag, eng in (("--oext-78b", "X"), ("--oext-78b-y", "Y")):
            code, out, err = call(mk.main, ["--pins", str(p), "--settings-dir", str(D), flag, fam])
            assert code == 0, err
            forms[(fam, eng)] = json.loads(out)
    checks = {}
    for fam in FAMS:
        for eng in ("X", "Y"):
            idx = D / mk.index_name(fam, eng)
            argv = ["check", "--family", fam, "--engine", eng, "--index", str(idx), "--index-sha256", sha(idx)]
            if pins["families"][fam]["w1_18"]["record_sha256"] is not None:
                argv += ["--w1-18-record", str(records[fam])]
            code, out, err = call(w.main, argv)
            checks[(fam, eng)] = (code, err.strip()[-200:])
    return files, forms, checks


base_pins, _ = mk.load_pins()
base_files, base_forms, base_checks = state(copy.deepcopy(base_pins), {})
assert all(c == 0 for c, _ in base_checks.values()), base_checks
# records under the base W1-18 settings: a branch fill does not change the W1-18 settings, so they stay valid
REC = {}
for fam in FAMS:
    REC[(fam, True)] = record_for(fam, WORK / "records", True)
    REC[(fam, False)] = record_for(fam, WORK / "records", False)

K1_THETA0 = {"olmo2-7b": "c91a7b3174a94cd75176a374c0c7acd2be04eb7527642179a89b763aad6cfabb",   # R-2 (r1-k1.md)
             "llama31-8b": "cd5976a60fdb04fe4db977c747d29a2110b7f66fe65b0f1e34447b196cef14a7"}


def fill_branch(fam, kind):
    def f(p, recs):
        if kind == "128":
            path, digest = REC[(fam, True)]
            p["families"][fam]["w1_18"] = {"branch": "128", "record_sha256": digest, "full_reason": None}
            recs[fam] = path
        elif kind == "full-record":
            path, digest = REC[(fam, False)]
            p["families"][fam]["w1_18"] = {"branch": "full", "record_sha256": digest, "full_reason": None}
            recs[fam] = path
        else:
            p["families"][fam]["w1_18"] = {"branch": "full", "record_sha256": None,
                                           "full_reason": "the W1-18 check could not run (a re-verifier stand-in)"}
    return f


def fill_theta0(fam):
    def f(p, recs):
        p["families"][fam]["units"]["untuned"]["job_sha256"] = K1_THETA0[fam]
    return f


def fill_g(fam, name):
    def f(p, recs):
        p["families"][fam]["recipe_g"] = cfg(name)
    return f


def fill_bqi(fam, name):
    def f(p, recs):
        p["families"][fam]["recipe_bqi"] = cfg(name)
    return f


def fill_engine_y(p, recs):
    p["shared"]["engine_y"] = "3" * 64


FILLS = {}
for fam in FAMS:
    for kind in ("128", "full-record", "full-reason"):
        FILLS[f"{fam} branch {kind}"] = (fill_branch(fam, kind), {(fam, "X"), (fam, "Y")})
    FILLS[f"{fam} theta0 job pin"] = (fill_theta0(fam), {(fam, "X"), (fam, "Y")})
FILLS["llama31-8b recipe G (1e-4 G stand-in)"] = (fill_g("llama31-8b", "study-kt-llama31-8b-r64-g-mb2-20261011"),
                                                  {("llama31-8b", "X")})
FILLS["olmo2-7b recipe G re-pin (b5e5 stand-in)"] = (fill_g("olmo2-7b", "study-kt-olmo2-7b-r64-b5e5-mb2-20261011"),
                                                     {("olmo2-7b", "X")})
FILLS["olmo2-7b recipe B+Qi (b5e5 stand-in)"] = (fill_bqi("olmo2-7b", "study-kt-olmo2-7b-r64-b5e5-mb2-20261011"),
                                                 {("olmo2-7b", "Y")})
FILLS["llama31-8b recipe B+Qi (MAIN stand-in)"] = (fill_bqi("llama31-8b", "study-kt-llama31-8b-r64-b5e5-mb2-20261010"),
                                                   {("llama31-8b", "Y")})
FILLS["shared ENGINE_Y"] = (fill_engine_y, {("olmo2-7b", "Y"), ("llama31-8b", "Y")})

ok = True
print(f"wrapper {wrapper_sha0[:12]}; base checks all exit 0: {all(c == 0 for c, _ in base_checks.values())}")
for name, (change, allowed) in FILLS.items():
    p, recs = copy.deepcopy(base_pins), {}
    change(p, recs)
    files, forms, checks = state(p, recs)
    fchanged = sorted(n for n in files if files[n] != base_files.get(n))
    fam_of = lambda n: "olmo2-7b" if "olmo2-7b" in n else "llama31-8b"
    eng_of = lambda n: "Y" if ("_y__" in n or "OEXT-78B-Y" in n) else ("XY" if "limits" in n else "X")
    reach = {(fam_of(n), e) for n in fchanged for e in eng_of(n) if e in "XY"}
    changed = {k for k in base_forms if base_forms[k] != forms[k]}
    wr = {k: forms[k]["files"]["scripts/scale78b/oext_78b.py"] for k in forms}
    good = changed == allowed and all(v == wrapper_sha0 for v in wr.values()) and \
        all(c == 0 for c, _ in checks.values()) and reach <= allowed | {(f, "Y") for f, e in allowed if False}
    ok &= good
    print(f"{'OK ' if good else 'BAD'} {name:44s} forms {sorted(f'{e}[{f}]' for f, e in changed)}; "
          f"files {fchanged}; checks {sorted({c for c, _ in checks.values()})}")
    if not all(c == 0 for c, _ in checks.values()):
        print("    ", {k: v for k, v in checks.items() if v[0] != 0})

# T-O2's order, cumulative: after a form's last input is filled, no later fill changes it
order = [("olmo2-7b theta0 job pin",), ("llama31-8b theta0 job pin",), ("olmo2-7b branch 128",),
         ("llama31-8b recipe G (1e-4 G stand-in)",), ("llama31-8b branch full-record",), ("shared ENGINE_Y",),
         ("olmo2-7b recipe B+Qi (b5e5 stand-in)",), ("llama31-8b recipe B+Qi (MAIN stand-in)",)]
p, recs = copy.deepcopy(base_pins), {}
prev = base_forms
history = []
for (step,) in order:
    if " branch " in step:            # records made under the W1-18 settings now in D (after the theta0 fills)
        fam = step.split()[0]
        REC[(fam, True)] = record_for(fam, WORK / "records-cumulative", True)
        REC[(fam, False)] = record_for(fam, WORK / "records-cumulative", False)
    FILLS[step][0](p, recs)
    files, forms, checks = state(p, recs)
    changed = sorted(f"{e}[{f}]" for (f, e) in forms if forms[(f, e)] != prev[(f, e)])
    history.append((step, changed, sorted({c for c, _ in checks.values()})))
    prev = forms
print("cumulative, T-O2 order:")
for step, changed, codes in history:
    print(f"  {step:44s} -> {changed}  checks {codes}")
last = {}
for i, (step, changed, _) in enumerate(history):
    for k in changed:
        last[k] = i
print("  last change per form:", {k: history[v][0] for k, v in sorted(last.items())})
assert hashlib.sha256(WRAPPER.read_bytes()).hexdigest() == wrapper_sha0
shutil.rmtree(D)
print("ALL OK" if ok else "SOME BAD")
