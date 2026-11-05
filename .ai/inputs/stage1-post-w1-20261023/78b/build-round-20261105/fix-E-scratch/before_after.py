"""Before/after evidence for fix round 3 of track E. A scratch root (symlinks to the read-only worktree, real copies of
scripts/stage1 and scripts/scale78b) runs the new test file against: the fixed wrapper (baseline); the round-3 wrapper
(the verifier's pristine copy, its index literal re-pinned to the current PINS-78B.json so it fails for the real
reasons); the m09 and m10 mutants of the fixed wrapper (verify-E's survivors). Summary lines and the first assertion
line per failure are recorded; no study text is read."""
import json, re, shutil, subprocess
from pathlib import Path

S = Path(__file__).resolve().parent
W = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-e")
PRISTINE_SW = S.parent / "verify-E-scratch" / "pristine-scale78b" / "scorers_78b.py"
R = S / "mutroot"
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
TEST = "scripts/scale78b/tests/scorers/test_untuned_two_calls_78b.py"
LOG = S / "before-after.jsonl"
M09 = ("        if item == flag and k + 1 < len(argv):\n            value = argv[k + 1]",
       "        if item == flag and k + 1 < len(argv) and value is None:\n            value = argv[k + 1]")
M10 = ('"command": checked["command"], "exit_code": code,', '"command": checked["command"], "exit_code": 0,')


def build_root():
    if R.exists():
        shutil.rmtree(R)
    R.mkdir()
    for entry in W.iterdir():
        if entry.name != "scripts":
            (R / entry.name).symlink_to(entry)
    (R / "scripts").mkdir()
    for entry in (W / "scripts").iterdir():
        if entry.name not in ("scale78b", "stage1"):
            (R / "scripts" / entry.name).symlink_to(entry)
    shutil.copytree(W / "scripts" / "stage1", R / "scripts" / "stage1")


def fresh_scale78b() -> Path:
    t = R / "scripts" / "scale78b"
    if t.exists():
        shutil.rmtree(t)
    shutil.copytree(W / "scripts" / "scale78b", t)
    return t


def mutate(t: Path, old: str, new: str):
    p = t / "scorers_78b.py"
    text = p.read_text(encoding="utf-8")
    assert text.count(old) == 1, old[:50]
    p.write_text(text.replace(old, new), encoding="utf-8")


def pristine_wrapper(t: Path):
    current = re.search(r'PINS_FILE_SHA256 = "([0-9a-f]{64})"', (W / "scripts/scale78b/scorers_78b.py").read_text()).group(1)
    text = PRISTINE_SW.read_text(encoding="utf-8")
    assert 'PINS_FILE_SHA256 = "cba2f0b290842eda03217ebfbffc01471f9febda543b84cf190937b91e544986"' in text
    (t / "scorers_78b.py").write_text(re.sub(r'PINS_FILE_SHA256 = "[0-9a-f]{64}"', f'PINS_FILE_SHA256 = "{current}"', text), encoding="utf-8")


def run(label: str):
    proc = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", TEST], cwd=R, capture_output=True,
                          text=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": "/Users/spiderishi"})
    lines = [l for l in (proc.stdout + proc.stderr).splitlines() if l.strip()]
    failed = [l.split(" - ")[0].replace("FAILED ", "") for l in lines if l.startswith("FAILED ")]
    reasons = [l[:200] for l in lines if l.startswith("E ")][:8]
    row = {"variant": label, "pytest_exit": proc.returncode, "summary": lines[-1] if lines else "(no output)",
           "failed": failed, "first_assertion_lines": reasons}
    print(json.dumps(row))
    with LOG.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


INDEX_OLD = "def load_pins_index(path: Path = PINS_FILE, expected_sha256: str = PINS_FILE_SHA256) -> dict:\n    try:"
INDEX_NEW = ("def load_pins_index(path: Path | None = None, expected_sha256: str | None = None) -> dict:\n"
             "    path = PINS_FILE if path is None else path\n"
             "    expected_sha256 = PINS_FILE_SHA256 if expected_sha256 is None else expected_sha256\n    try:")
VARIANTS = {
    "baseline": lambda t: None,
    "pristine": pristine_wrapper,
    "pristine+index": lambda t: (pristine_wrapper(t), mutate(t, INDEX_OLD, INDEX_NEW)),
    "m09": lambda t: mutate(t, *M09),
    "m10": lambda t: mutate(t, *M10),
}
LABELS = {"baseline": "fixed wrapper (baseline)",
          "pristine": "round-3 wrapper (verify-E's pristine copy, index literal re-pinned)",
          "pristine+index": "round-3 wrapper + only the load_pins_index call-time defaults (so the synthetic family installs)",
          "m09": "m09 flag_value first-not-last on the fixed wrapper",
          "m10": "m10 record exit_code always 0 on the fixed wrapper"}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(VARIANTS)
    build_root()
    for name in names:
        t = fresh_scale78b()
        VARIANTS[name](t)
        run(LABELS[name])
    shutil.rmtree(R)
    print("mutroot removed")
