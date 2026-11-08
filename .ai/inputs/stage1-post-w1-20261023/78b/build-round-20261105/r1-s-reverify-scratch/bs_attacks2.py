"""Re-verifier's blinding attacks on blinded_sigma.py (fix round, 6e7079e8...): the first verifier's five CLI cases
re-run, plus attacks on the new code paths (the engine-per-role map, the --out folder refusal, the exclusive create,
full-line refusals). Every case runs the CLI from a fresh cwd, snapshots EVERY file under the scratch root (fixture,
cwd, out folders) and the WS package before and after, and scans stdout, stderr and every new file for the planted
values (the test's sentinels plus raw counts, k/60, Fraction(k, 0) and quoted counts). It prints, per case, the exit
status, the stderr line (refusal texts hold no fixture value by construction; the scan is printed as a boolean and a
count only), new files and changed files. Synthetic fixture only (the test module's helpers, imported read-only).
Usage: PY -B bs_attacks2.py WS SCRATCH_ROOT"""
import json, os, pathlib, shutil, stat, subprocess, sys
ws, tmp = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sys.path.insert(0, str(ws))
from scripts.scale78b.tests import test_blinded_sigma as T
from scripts.scale78b import blinded_sigma as bs

SCRIPT = ws / "scripts/scale78b/blinded_sigma.py"
root = tmp / "fx"
fams = {f: T.build_family(root, f) for f in ("olmo2-7b", "llama31-8b")}
split = T.build_family(root / "engines", "olmo2-7b", engines=T.ENGINES_SPLIT)
for arm, by_seed in split["cells"].items():
    for entry in by_seed.values():
        entry["path"] = "engines/" + entry["path"]
marks = T.sentinels()
counts = {T.unsafe_count(f, a, s) for f in fams for (a, s) in bs.design_cells("full")}
extra = {f"Fraction({k}, 0)" for k in counts} | {f"{k}/60" for k in counts} | {f"'{k}'" for k in counts}
WATCH = (tmp, ws / "scripts/scale78b")


def snapshot():
    out = {}
    for folder in WATCH:
        for p in pathlib.Path(folder).rglob("*"):
            if p.is_symlink():
                out[str(p)] = "link:" + os.readlink(p)
            elif p.is_file():
                try:
                    out[str(p)] = T.sha(p.read_bytes())
                except PermissionError:
                    out[str(p)] = "unreadable"
    return out


def reseal(folder):
    marker = json.loads((folder / "COMPLETE.json").read_bytes())
    for rel in list(marker["files"]):
        marker["files"][rel] = T.sha((folder / rel).read_bytes())
    (folder / "COMPLETE.json").write_bytes(T.canon(marker))
    return T.sha((folder / "COMPLETE.json").read_bytes())


def scan(texts):
    return sorted({m for m in marks | extra for t in texts if m in t})


def run(label, families, option="B", out=None, name=None, expect=None):
    inputs, digest = T.write_inputs(root, option, families, f"inputs-{name or label}.json")
    cwd = tmp / f"cwd-{label}"
    cwd.mkdir()
    before = snapshot()
    args = [sys.executable, "-I", "-B", str(SCRIPT), "--inputs", str(inputs), "--inputs-sha256", digest]
    if out is not None:
        args += ["--out", str(out)]
    r = subprocess.run(args, capture_output=True, text=True, cwd=cwd)
    after = snapshot()
    new = sorted(set(after) - set(before))
    changed = sorted(k for k in before if after.get(k) != before[k])
    texts = [r.stdout, r.stderr] + [pathlib.Path(n).read_text(errors="replace") for n in new if pathlib.Path(n).is_file()]
    hits = scan(texts)
    line = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ""
    res = {"case": label, "exit": r.returncode, "stdout_bytes": len(r.stdout), "stderr_lines": len(r.stderr.splitlines()),
           "stderr_last": line[-170:], "new": [str(pathlib.Path(n).relative_to(tmp)) if n.startswith(str(tmp)) else n for n in new],
           "changed": changed, "planted_found": len(hits)}
    if expect is not None:
        res["stderr_exact"] = r.stderr == expect + "\n"
    print(json.dumps(res), flush=True)
    return r


def tamper_case(label, tamper, out=None, cell=("olmo2-7b", "S1", "1103"), expect=None):
    f2 = json.loads(json.dumps(fams))
    fam, arm, seed = cell
    src = root / f2[fam]["cells"][arm][seed]["path"]
    dst = root / f"t-{label}"
    shutil.copytree(src, dst)
    tamper(dst)
    entry = {k: v for k, v in f2[fam]["cells"][arm][seed].items() if k not in ("path", "complete_sha256")}
    f2[fam]["cells"][arm][seed] = {**entry, "path": f"t-{label}", "complete_sha256": reseal(dst)}
    return run(label, f2, out=out, expect=expect)


def edit_summary(change):
    def go(d):
        s = json.loads((d / "eval/e1/summary.json").read_bytes()); change(s)
        (d / "eval/e1/summary.json").write_bytes(T.canon(s))
    return go


def edit_jsonl(name, change):
    def go(d):
        lines = (d / "eval/e1" / name).read_text().splitlines()
        first = json.loads(lines[0]); change(first); lines[0] = json.dumps(first)
        (d / "eval/e1" / name).write_text("\n".join(lines) + "\n")
    return go


outs = tmp / "outs"
outs.mkdir()
# --- the first verifier's five cases, re-run -----------------------------------------------------------------------
tamper_case("zero-answers", edit_summary(lambda s: s["harm"]["sampled"].__setitem__("answers", 0)), outs / "o-zero.json",
            expect="blinded_sigma: unexpected error (ZeroDivisionError); nothing written")
tamper_case("string-count", edit_summary(lambda s: s["harm"]["sampled"].__setitem__("unsafe", str(s["harm"]["sampled"]["unsafe"]))),
            outs / "o-string.json")
tamper_case("bad-repetition", edit_jsonl("samples.jsonl", lambda r: r.__setitem__("repetition_4gram", "0.61666x")))
tamper_case("missing-guard-key", edit_jsonl("guard_samples.jsonl", lambda r: r.pop("prompt_id")))
run("out-dir-missing", fams, out=tmp / "no-such-dir" / "o.json", expect="--out's folder does not exist: nothing written")
# --- new: late refusals at the last cell read (every other U already in memory) ---------------------------------------
tamper_case("late-overrefusal", edit_summary(lambda s: s["overrefusal"].__setitem__("refusals", 3)), outs / "o-late.json",
            cell=("olmo2-7b", "a0", "1104"),
            expect="olmo2-7b a0@1104: the over-refusal guard records disagree with summary.json")
tamper_case("late-zero-answers", edit_summary(lambda s: s["harm"]["sampled"].__setitem__("answers", 0)), outs / "o-late0.json",
            cell=("olmo2-7b", "a0", "1104"), expect="blinded_sigma: unexpected error (ZeroDivisionError); nothing written")
tamper_case("late-unsafe-off-by-one", edit_summary(lambda s: s["harm"]["sampled"].__setitem__("unsafe", s["harm"]["sampled"]["unsafe"] + 1)),
            outs / "o-late1.json", cell=("olmo2-7b", "a0", "1104"))
# --- new: the engine-per-role map ---------------------------------------------------------------------------------------
for role in ("a0", "R", "block_a"):
    s2 = json.loads(json.dumps(split)); s2["engine"][role] = "5" * 64
    run(f"engine-{role}-wrong", {"olmo2-7b": s2}, option="C", out=outs / f"o-eng-{role}.json")
s2 = json.loads(json.dumps(split)); s2["engine"] = {"block_a": s2["engine"]["block_a"], "reused": s2["engine"]["a0"]}
run("engine-old-two-key-form", {"olmo2-7b": s2}, option="C", out=outs / "o-eng-old.json",
    expect="olmo2-7b: engine gives the a0, R and block_a code identities (64 hex each)")
s2 = json.loads(json.dumps(split)); s2["engine"]["extra"] = "6" * 64
run("engine-extra-key", {"olmo2-7b": s2}, option="C", expect="olmo2-7b: engine gives the a0, R and block_a code identities (64 hex each)")
s2 = json.loads(json.dumps(split)); s2["engine"]["a0"] = 17
run("engine-non-hex", {"olmo2-7b": s2}, option="C", expect="olmo2-7b: engine gives the a0, R and block_a code identities (64 hex each)")
s2 = json.loads(json.dumps(split)); s2["engine"]["a0"], s2["engine"]["R"] = s2["engine"]["R"], s2["engine"]["a0"]
run("engine-a0-R-swapped", {"olmo2-7b": s2}, option="C", expect="olmo2-7b R@1101: job.json code_sha256 is not the family's R value")
r = run("engine-split-good", {"olmo2-7b": split}, option="C", out=outs / "o-split.json")
# --- new: the --out paths ------------------------------------------------------------------------------------------------
(tmp / "a-file").write_text("x")
run("out-parent-is-a-file", fams, out=tmp / "a-file" / "o.json", expect="--out's folder does not exist: nothing written")
os.symlink(tmp / "dangling-target", outs / "dangling.json")
run("out-dangling-symlink", fams, out=outs / "dangling.json", expect="--out exists: the output is written once")
run("out-is-dev-stderr", fams, out=pathlib.Path("/dev/stderr"), expect="--out exists: the output is written once")
ro = tmp / "readonly"
ro.mkdir()
os.chmod(ro, stat.S_IRUSR | stat.S_IXUSR)
try:
    run("out-folder-read-only", fams, out=ro / "o.json", expect="blinded_sigma: unexpected error (PermissionError); nothing written")
finally:
    os.chmod(ro, stat.S_IRWXU)
# --- new: the exclusive create, in process: a file made between the existence check and the write --------------------
inputs, digest = T.write_inputs(root, "B", fams, "inputs-race.json")
race = outs / "race.json"
real_read = bs.read
def racing_read(*a, **k):
    doc = real_read(*a, **k)
    race.write_bytes(b"made meanwhile\n")
    return doc
bs.read = racing_read
try:
    import io, contextlib
    err, outbuf = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(outbuf), contextlib.redirect_stderr(err):
            bs.main(["--inputs", str(inputs), "--inputs-sha256", digest, "--out", str(race)])
        msg = None
    except SystemExit as exc:
        msg = str(exc)
    print(json.dumps({"case": "race-exclusive-create", "message": msg, "file_kept": race.read_bytes() == b"made meanwhile\n",
                      "stdout_bytes": len(outbuf.getvalue()), "stderr_bytes": len(err.getvalue())}), flush=True)
finally:
    bs.read = real_read
# --- new: the in-process API (bs.read, not main): an unexpected error's text reaches the caller unguarded -------------
f2 = json.loads(json.dumps(fams))
f2["olmo2-7b"]["cells"]["S1"]["1103"] = {"path": "t-zero-answers", "complete_sha256": T.sha((root / "t-zero-answers/COMPLETE.json").read_bytes())}
inputs, digest = T.write_inputs(root, "B", f2, "inputs-inproc.json")
try:
    bs.read(inputs, digest)
    print(json.dumps({"case": "in-process-read-zero-answers", "raised": None}))
except SystemExit as exc:
    print(json.dumps({"case": "in-process-read-zero-answers", "raised": "SystemExit", "planted_found": len(scan([str(exc)]))}))
except Exception as exc:
    print(json.dumps({"case": "in-process-read-zero-answers", "raised": type(exc).__name__,
                      "planted_found_in_message": len(scan([str(exc)]))}), flush=True)
