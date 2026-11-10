"""O6 re-check: the documented fill procedure, done in place in a scratch copy of WS (scripts/scale78b copied, every
other entry linked read-only, as the mutation runner does), then the whole scale78b suite in that copy.

    PY -B rv_fill.py WS SCRATCH SCENARIO        (SCENARIO: theta0-olmo | branch-olmo | everything)

The documented procedure (make_oext_settings_78b.py:38-41): edit settings/oext_pins_78b.json; run the maker (it writes
the files); run the tests. The pins file and the settings are the copy's own (the maker's defaults). No real unit,
record or answer is read; the W1-18 record of a branch fill is a synthetic text-free stand-in.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WS, SCRATCH, SCENARIO = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
if SCRATCH.exists():
    raise SystemExit(f"{SCRATCH} exists")
repo = SCRATCH / "repo"
(repo / "scripts").mkdir(parents=True)
for entry in sorted(WS.iterdir()):
    if entry.name not in ("scripts", ".git"):
        (repo / entry.name).symlink_to(entry.resolve())
for entry in sorted((WS / "scripts").iterdir()):
    if entry.name == "scale78b":
        shutil.copytree(entry, repo / "scripts" / "scale78b", symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    else:
        (repo / "scripts" / entry.name).symlink_to(entry.resolve())

settings = repo / "scripts/scale78b/settings"
pins_path = settings / "oext_pins_78b.json"
K1_THETA0 = {"olmo2-7b": "c91a7b3174a94cd75176a374c0c7acd2be04eb7527642179a89b763aad6cfabb",   # R-2 (r1-k1.md)
             "llama31-8b": "cd5976a60fdb04fe4db977c747d29a2110b7f66fe65b0f1e34447b196cef14a7"}
sys.path.insert(0, str(WS))
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402
BQI_OLMO = config_sha256(load_recipe(WS / "experiments/safety_selection/configs/study-kt-olmo2-7b-r64-b5e5-mb2-20261011.json"))
env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
env["PYTHONDONTWRITEBYTECODE"] = "1"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(doc):
    return (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def maker():
    done = subprocess.run([sys.executable, "-B", "scripts/scale78b/make_oext_settings_78b.py"], cwd=repo, env=env,
                          capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-400:]


def record(family):
    lim = json.loads((settings / f"limits_overrefusal_checks__{family}.json").read_bytes())
    doc = {"kind": "stage1 over-refusal checks", "version": 1,
           "units": {n: {"truncation": {"cap_tokens": lim["truncation"]["cap_tokens"]}} for n in lim["units"]},
           "truncation_check": {"pass": True},
           "provenance": {"settings_sha256": sha(settings / f"limits_overrefusal_checks__{family}.json")}}
    path = SCRATCH / "records" / f"w1_18_record__{family}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(doc, sort_keys=True).encode())
    return sha(path)


pins = json.loads(pins_path.read_bytes())
steps = []
if SCENARIO in ("theta0-olmo", "branch-olmo", "everything"):
    pins["families"]["olmo2-7b"]["units"]["untuned"]["job_sha256"] = K1_THETA0["olmo2-7b"]
    steps.append("theta0 olmo2-7b")
if SCENARIO in ("branch-olmo", "everything"):
    pins["families"]["llama31-8b"]["units"]["untuned"]["job_sha256"] = K1_THETA0["llama31-8b"]
    steps.append("theta0 llama31-8b")
pins_path.write_bytes(dump(pins))
maker()
if SCENARIO in ("branch-olmo", "everything"):
    fams = ["olmo2-7b"] if SCENARIO == "branch-olmo" else ["olmo2-7b", "llama31-8b"]
    for fam in fams:
        pins["families"][fam]["w1_18"] = {"branch": "128", "record_sha256": record(fam), "full_reason": None}
        steps.append(f"branch 128 {fam}")
if SCENARIO == "everything":
    # stand-ins chosen to differ from the suite's own stand-ins (the suite fills G with the 1e-4 G config and B+Qi
    # with MAIN): Llama's G = its MAIN config (same blocks); B+Qi = the b5e5 config (OLMo) and MAIN (Llama)
    pins["families"]["llama31-8b"]["recipe_g"] = dict(pins["families"]["llama31-8b"]["main"])
    pins["shared"]["engine_y"] = "3" * 64
    pins["families"]["olmo2-7b"]["recipe_bqi"] = {"name": "study-kt-olmo2-7b-r64-b5e5-mb2-20261011",
                                                  "config_sha256": BQI_OLMO}
    pins["families"]["llama31-8b"]["recipe_bqi"] = dict(pins["families"]["llama31-8b"]["main"])
    steps += ["recipe G llama31-8b (MAIN stand-in)", "ENGINE_Y", "B+Qi both (stand-ins)"]
pins_path.write_bytes(dump(pins))
maker()
check = subprocess.run([sys.executable, "-B", "scripts/scale78b/make_oext_settings_78b.py", "--check"], cwd=repo,
                       env=env, capture_output=True, text=True, timeout=300)
print(f"scenario {SCENARIO}: steps {steps}; maker --check exit {check.returncode}")
cmd = [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfE", "--basetemp",
       str(SCRATCH / "pt"), "scripts/scale78b/tests"]
done = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=560)
lines = [x for x in (done.stdout + done.stderr).splitlines() if x.strip()]
print(f"suite exit {done.returncode}: {lines[-1] if lines else ''}")
for x in lines:
    if x.startswith(("FAILED ", "ERROR ")):
        print("  ", x[:260])
