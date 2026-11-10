"""Verifier: the 1B pair's difference, the two 7-8B main configs' hashes and identities by the engine's functions,
the maker's output (synthetic anchor hash, into the scratch folder) diffed and loaded. Run with the main venv -I -B."""
import json, pathlib, subprocess, sys
WS = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-c")
OUT = pathlib.Path(__file__).resolve().parent / "s78-out"
sys.path.insert(0, str(WS))
from experiments.safety_selection.config import config_sha256, load_recipe, training_identity, validate_recipe
C = WS / "experiments/safety_selection/configs"


def diff(a, b, prefix=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = set()
        for k in set(a) | set(b):
            p = f"{prefix}.{k}" if prefix else k
            out |= {p} if (k not in a or k not in b) else diff(a[k], b[k], p)
        return out
    return set() if a == b else {prefix}


rec = json.loads((C / "study-kt-olmo2-1b-r64-b-mb4-20261008.json").read_text())
s1b = json.loads((C / "study-kt-olmo2-1b-r64-b-mb4-gateb-20261008.json").read_text())
print("1B REC", config_sha256(rec)[:16], "S", config_sha256(s1b)[:16], "ti", training_identity(rec)[:16], training_identity(s1b)[:16])
print("1B pair diff:", sorted(diff(rec, s1b)))
print("1B S attribution:", {k: (v if k != "query_bank" else v[:16] + "...") for k, v in s1b["attribution"].items()})
print("1B REC attribution:", rec["attribution"])
mains = {"olmo2-7b": "study-kt-olmo2-7b-r64-b-mb2-20261008.json", "llama31-8b": "study-kt-llama31-8b-r64-b5e5-mb2-20261010.json"}
synthetic = "ab" * 32
OUT.mkdir(exist_ok=True)
for fam, f in mains.items():
    main = load_recipe(C / f)
    print(f"\n{fam} main {f}: config_sha256 {config_sha256(main)} training_identity {training_identity(main)}")
    print("   main attribution:", main["attribution"], "| attribution diff vs 1B REC:", sorted(diff(rec["attribution"], main["attribution"])))
    name = f.replace("-20261008.json", "").replace("-20261010.json", "") + "-gateb-20261105"
    out = OUT / f"{name}.json"
    if out.exists():
        out.unlink()
    cmd = [sys.executable, "-I", "-B", str(WS / "scripts/scale78b/make_recipe_s78.py"), "--family", fam, "--anchors-sha256", synthetic, "--out", str(out)]
    run = subprocess.run(cmd, capture_output=True, text=True)
    print("   maker exit", run.returncode, run.stdout.strip()[:200], run.stderr.strip()[:200])
    s78 = load_recipe(out)                         # the engine's loader
    print("   S_78 loaded; config_sha256", config_sha256(s78)[:16], "training_identity", training_identity(s78)[:16],
          "equal to main's:", training_identity(s78) == training_identity(main))
    d = sorted(diff(main, s78))
    print("   diff S_78 vs main:", d, "| equals 1B pair's set:", set(d) == diff(rec, s1b))
    print("   S_78 attribution:", {k: (v if k != "query_bank" else v[:12] + "...") for k, v in s78["attribution"].items()})
    print("   key order kept:", list(s78) == list(main), "| indent:", len((out.read_text().splitlines()[1])) - len(out.read_text().splitlines()[1].lstrip()),
          "main indent:", len(((C / f).read_text().splitlines()[1])) - len((C / f).read_text().splitlines()[1].lstrip()))
    print("   purpose length:", len(s78["purpose"]))
