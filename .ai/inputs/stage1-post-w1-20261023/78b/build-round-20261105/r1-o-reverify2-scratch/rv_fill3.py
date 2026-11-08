"""Re-verifier's in-place fill check, second pass (my own rv_fill.py, extended for R-21's record place; not the
builder's rv_fill2.py). One scratch copy of WS: scripts/scale78b copied; every other scripts/ entry and top-level entry
linked read-only; .ai mirrored by links except the folders along R-21's record folder, which are real, so a record
can be committed there without touching WS. Starting from the COMMITTED pins (not a reconstructed state), the T-O2
steps are applied cumulatively, in place, with the maker's defaults; after each state the maker's --check and the
whole scale78b suite run in the copy.

    PY -B rv_fill3.py WS SCRATCH FROM TO        (states FROM..TO, 0 = the committed state; FROM 0 builds the copy)

My values differ from the suite's own stand-ins where a real choice exists: theta0 = K1's measured job pins (R-2);
B+Qi = a config with MAIN's blocks that is not MAIN (OLMo: its G config; Llama: the 1e-4 G config). Records are
synthetic, text-free, made under the copy's W1-18 settings at the time of the branch fill.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

WS, SCRATCH, FROM, TO = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), int(sys.argv[3]), int(sys.argv[4])
RECORDS = ".ai/inputs/stage1-post-w1-20261023/78b/w1-18"
repo = SCRATCH / "repo"
settings = repo / "scripts/scale78b/settings"
pins_path = settings / "oext_pins_78b.json"
env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTEST_ADDOPTS", "PYTEST_PLUGINS",
                                                        "OEXT78_NESTED")}
env["PYTHONDONTWRITEBYTECODE"] = "1"


def mirror(src: Path, dst: Path, real_parts: list) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    keep = real_parts[0] if real_parts else None
    if src.is_dir():
        for e in sorted(src.iterdir()):
            if e.name != keep:
                (dst / e.name).symlink_to(e.resolve())
    if keep is not None:
        mirror(src / keep, dst / keep, real_parts[1:])


if FROM == 0:
    if SCRATCH.exists():
        raise SystemExit(f"{SCRATCH} exists")
    (repo / "scripts").mkdir(parents=True)
    for e in sorted(WS.iterdir()):
        if e.name not in ("scripts", ".git", ".ai"):
            (repo / e.name).symlink_to(e.resolve())
    for e in sorted((WS / "scripts").iterdir()):
        if e.name == "scale78b":
            subprocess.run(["rsync", "-a", "--exclude", "__pycache__", f"{e}/", f"{repo / 'scripts/scale78b'}/"],
                           check=True)
        else:
            (repo / "scripts" / e.name).symlink_to(e.resolve())
    mirror(WS / ".ai", repo / ".ai", RECORDS.split("/")[1:])
    assert (repo / RECORDS).is_dir() and not (repo / RECORDS).is_symlink()
    for part in range(1, len(RECORDS.split("/")) + 1):
        assert not (repo / "/".join(RECORDS.split("/")[:part])).is_symlink()
    assert pins_path.read_bytes() == (WS / "scripts/scale78b/settings/oext_pins_78b.json").read_bytes()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def dump(doc):
    return (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def cfg(name):
    sys.path.insert(0, str(WS))
    from experiments.safety_selection.config import config_sha256, load_recipe
    return {"name": name, "config_sha256": config_sha256(load_recipe(WS / "experiments/safety_selection/configs" /
                                                                     f"{name}.json"))}


def record(family, passed):
    lim_path = settings / f"limits_overrefusal_checks__{family}.json"
    lim = json.loads(lim_path.read_bytes())
    doc = {"kind": "stage1 over-refusal checks", "version": 1,
           "units": {n: {"truncation": {"cap_tokens": lim["truncation"]["cap_tokens"]}} for n in lim["units"]},
           "truncation_check": {"pass": passed}, "provenance": {"settings_sha256": sha(lim_path)}}
    rel = f"{RECORDS}/w1_18_record__{family}.json"
    (repo / rel).write_bytes(json.dumps(doc, sort_keys=True).encode())
    return rel, sha(repo / rel)


K1_THETA0 = {"olmo2-7b": "c91a7b3174a94cd75176a374c0c7acd2be04eb7527642179a89b763aad6cfabb",
             "llama31-8b": "cd5976a60fdb04fe4db977c747d29a2110b7f66fe65b0f1e34447b196cef14a7"}


def step(k, p):
    fam = p["families"]
    if k == 1:
        fam["olmo2-7b"]["units"]["untuned"]["job_sha256"] = K1_THETA0["olmo2-7b"]
    elif k == 2:
        fam["llama31-8b"]["units"]["untuned"]["job_sha256"] = K1_THETA0["llama31-8b"]
    elif k == 3:
        rel, h = record("olmo2-7b", True)
        fam["olmo2-7b"]["w1_18"] = {"branch": "128", "record_sha256": h, "record_path": rel, "full_reason": None}
    elif k == 4:
        fam["llama31-8b"]["recipe_g"] = cfg("study-kt-llama31-8b-r64-g-mb2-20261011")
    elif k == 5:
        rel, h = record("llama31-8b", False)
        fam["llama31-8b"]["w1_18"] = {"branch": "full", "record_sha256": h, "record_path": rel, "full_reason": None}
    elif k == 6:
        p["shared"]["engine_y"] = "3" * 64
    elif k == 7:
        fam["olmo2-7b"]["recipe_bqi"] = cfg("study-kt-olmo2-7b-r64-g-mb2-20261011")
    elif k == 8:
        fam["llama31-8b"]["recipe_bqi"] = cfg("study-kt-llama31-8b-r64-g-mb2-20261011")
    return ["committed", "theta0 olmo2-7b", "theta0 llama31-8b", "branch 128 olmo2-7b", "recipe G llama31-8b",
            "branch full llama31-8b (failing record)", "ENGINE_Y", "B+Qi olmo2-7b", "B+Qi llama31-8b"][k]


def run(args, timeout=560):
    return subprocess.run([sys.executable, "-B", *args], cwd=repo, env=env, capture_output=True, text=True,
                          timeout=timeout)


for k in range(FROM, TO + 1):
    pins = json.loads(pins_path.read_bytes())
    name = step(k, pins)
    if k > 0:
        pins_path.write_bytes(dump(pins))
    made = run(["scripts/scale78b/make_oext_settings_78b.py"], 300)
    check = run(["scripts/scale78b/make_oext_settings_78b.py", "--check"], 300)
    done = run(["-m", "pytest", "-p", "no:cacheprovider", "-q", "-rfE", "--basetemp", str(SCRATCH / f"pt-{k}"),
                "scripts/scale78b/tests"])
    subprocess.run(["rm", "-rf", str(SCRATCH / f"pt-{k}")])
    lines = [x for x in (done.stdout + done.stderr).splitlines() if x.strip()]
    fails = [x for x in lines if x.startswith(("FAILED ", "ERROR "))]
    track_o = [x for x in fails if "/tests/oext/" in x]
    print(f"state {k} ({name}): maker exit {made.returncode}, --check exit {check.returncode}; suite exit "
          f"{done.returncode}: {lines[-1] if lines else ''}; Track O failures {len(track_o)}; other {len(fails) - len(track_o)}",
          flush=True)
    for x in fails:
        print("   ", x[:230], flush=True)
