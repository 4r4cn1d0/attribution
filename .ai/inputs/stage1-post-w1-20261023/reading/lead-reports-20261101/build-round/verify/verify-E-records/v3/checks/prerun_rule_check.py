"""Synthetic reproduction of LR R6.1 as the fix-round-2 drafts state it (track A's builder in ws-a on its own synthetic
kit; no real data; nothing written outside <scratch>).

Claims checked (E-D5-D6.md items 4 and 8; E-39.md 8(d)(iii); E-plan-updates.md item 3):
 1. R1b with --coherent-out, step 2 with --coherent-out: R1D:582-598's comparison fails on coherent.output_sha256
    alone, and passes once that key is left out (the rule the drafts state).
 2. tables.json is byte-identical with and without --coherent-out (same overlap setting), for the pre-run and step 2.
 3. The counts document binds tables.json (input_sha256 = SHA-256 of tables.json) and its cells are the same with and
    without the overlap block (the counts' checks do not depend on the overlap block).
 4. A refusal only on a coherent-only check: exit 2, stderr names the counts, nothing written; the same build without
    the option passes, and its tables.json equals the with-option build's (the (c) route at the pre-run).
Usage: python -B prerun_rule_check.py <ws-a root> <scratch folder>
"""
import contextlib
import hashlib
import io
import json
import pathlib
import sys

ws, scratch = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sys.path.insert(0, str(ws))
sys.path.insert(0, str(ws / "scripts/stage1_s1/reading_input/tests"))
import synth_kit as sk  # noqa: E402
from scripts.stage1_s1.reading_input import items as it  # noqa: E402
from scripts.stage1_s1.reading_input.__main__ import main  # noqa: E402

s = sk.make(scratch / "world", "plan_a")
results = {}


def build(tag, overlap, counts):
    d = scratch / tag
    d.mkdir()
    args = s.args(d / "tables.json", d / "sources.json", overlap=overlap)
    if counts:
        args += ["--coherent-out", str(d / "counts.json")]
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = main(args)
    return rc, d, out.getvalue(), err.getvalue()


def load(q):
    return json.loads(q.read_text())


def sha(q):
    return hashlib.sha256(q.read_bytes()).hexdigest()


def r1d_compare(pre, inp, drop_coherent_hash):
    """R1D:582-598 (hb_tables left out: no --hb-out here), optionally with the drafts' rule for coherent.output_sha256."""
    t0, t1 = load(pre / "tables.json"), load(inp / "tables.json")
    s0, s1 = load(pre / "sources.json"), load(inp / "sources.json")
    t1.pop("overlap", None)
    for x in (s0, s1):
        x.pop("overlap", None)
        x.pop("output_sha256", None)
        (x.get("hb") or {}).pop("output_sha256", None)
        if drop_coherent_hash:
            (x.get("coherent") or {}).pop("output_sha256", None)
    return {"tables_without_overlap": t0 == t1, "sources_equal": s0 == s1}


rc_pre_c, pre_c, _, _ = build("prerun-with-counts", overlap=False, counts=True)
rc_pre_n, pre_n, _, _ = build("prerun-no-counts", overlap=False, counts=False)
rc_s2_c, s2_c, _, _ = build("step2-with-counts", overlap=True, counts=True)
rc_s2_n, s2_n, _, _ = build("step2-no-counts", overlap=True, counts=False)
results["exit codes (prerun+counts, prerun, step2+counts, step2)"] = [rc_pre_c, rc_pre_n, rc_s2_c, rc_s2_n]

# 1. the comparison with and without the drafts' rule
results["1a R1D comparison as drafted (coherent.output_sha256 kept)"] = r1d_compare(pre_c, s2_c, False)
results["1b with the drafts' rule (coherent.output_sha256 left out)"] = r1d_compare(pre_c, s2_c, True)
results["1c coherent block of sources.json (pre-run, step 2)"] = [load(pre_c / "sources.json")["coherent"],
                                                                load(s2_c / "sources.json")["coherent"]]

# 2. tables.json byte-identical with and without the option
results["2 tables.json identical without the option (pre-run, step 2)"] = [
    sha(pre_c / "tables.json") == sha(pre_n / "tables.json"), sha(s2_c / "tables.json") == sha(s2_n / "tables.json")]

# 3. the counts document binds tables.json; the cells do not depend on the overlap block
c_pre, c_s2 = load(pre_c / "counts.json"), load(s2_c / "counts.json")
results["3a counts input_sha256 = sha256(tables.json) (pre-run, step 2)"] = [
    c_pre["input_sha256"] == sha(pre_c / "tables.json"), c_s2["input_sha256"] == sha(s2_c / "tables.json")]
results["3b counts cells equal across the overlap block"] = c_pre["cells"] == c_s2["cells"]
results["3c tables.json differ by the overlap block only"] = (
    sha(pre_c / "tables.json") != sha(s2_c / "tables.json")
    and {k: v for k, v in load(pre_c / "tables.json").items() if k != "overlap"}
    == {k: v for k, v in load(s2_c / "tables.json").items() if k != "overlap"})

# 4. a refusal only on a coherent-only check at the pre-run, then the (c) route without the option
real = it.harm


def fake(*args, **kw):
    out = real(*args, **kw)
    out["coherent"] = {p: ((c[0] + 1, c[1], c[2]) if c[0] < 3 and c[2] <= 2 - c[0] else c)
                       for p, c in out["coherent"].items()}
    return out


it.harm = fake
rc_bad, bad, out_bad, err_bad = build("prerun-counts-refused", overlap=False, counts=True)
it.harm = real
results["4a refused pre-run: exit, stdout empty, stderr names the counts, nothing written"] = [
    rc_bad, out_bad == "", err_bad.strip()[:140], sorted(p.name for p in bad.iterdir())]
# the same (corrupted) builder without the option would pass: the (c) route needs only the option dropped
it.harm = fake
rc_bad_n, bad_n, _, _ = build("prerun-counts-refused-then-without-option", overlap=False, counts=False)
it.harm = real
results["4b the same build without the option: exit, tables.json equals the pre-run's"] = [
    rc_bad_n, sha(bad_n / "tables.json") == sha(pre_c / "tables.json")]

for k, v in results.items():
    print(k, "->", json.dumps(v, default=str))
ok = (results["1a R1D comparison as drafted (coherent.output_sha256 kept)"]["sources_equal"] is False
      and results["1b with the drafts' rule (coherent.output_sha256 left out)"] == {"tables_without_overlap": True, "sources_equal": True}
      and results["2 tables.json identical without the option (pre-run, step 2)"] == [True, True]
      and results["3a counts input_sha256 = sha256(tables.json) (pre-run, step 2)"] == [True, True]
      and results["3b counts cells equal across the overlap block"] is True
      and results["3c tables.json differ by the overlap block only"] is True
      and rc_bad == 2 and out_bad == "" and err_bad.startswith("REFUSED: the coherent-only counts")
      and sorted(p.name for p in bad.iterdir()) == []
      and rc_bad_n == 0 and results["4b the same build without the option: exit, tables.json equals the pre-run's"][1] is True)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
