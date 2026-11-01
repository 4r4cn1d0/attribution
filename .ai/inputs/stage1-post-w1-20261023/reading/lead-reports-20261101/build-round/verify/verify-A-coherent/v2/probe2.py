"""Verifier 2's probes (synthetic only): (1) coherent.check's bindings and refusals beyond the builder's cases; (2) the
reader's command line on refusal (exit 2, nothing written) and on duplicate JSON keys; (3) the stated binding limit
(a swap of two prompts with equal Unsafe counts but other splits; a Safe answer's failure moved) and its effect;
(4) extreme but legal counts (every cell empty; one coherent answer per cell; a whole cluster empty; a pair with
identical cells) never stop the S-G reading: the reader returns, every contrast is computable or 'not computable'
with p = 1, and the output is strict canonical JSON.

    PYTHONPATH=<ws-a> python -B probe2.py <scratch folder>
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gen2  # noqa: E402

from scripts.stage1_s1.reading.reading import read  # noqa: E402
from scripts.stage1_s1.reading.schema import validate  # noqa: E402
from scripts.stage1_s1.reading.settings import Refusal, canonical_json, sha256_bytes, strict_json  # noqa: E402
from scripts.stage1_s1.reading_input import coherent as coh  # noqa: E402
from scripts.stage1_s1.reading_input import sg_coherent as sgc  # noqa: E402

results = []


def note(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'OK  ' if ok else 'FAIL'} {name}: {detail}", flush=True)


def docs(reading, seed, **kw):
    tables, counts = gen2.world(reading, seed, kind=coh.KIND, rule=coh.RULE, **kw)
    tables = strict_json(canonical_json(tables))
    ts = sha256_bytes(canonical_json(tables))
    counts["input_sha256"] = ts
    counts = strict_json(canonical_json(counts))
    reading_doc = strict_json(canonical_json(read(tables, ts)))
    return tables, counts, reading_doc, ts


def run_sg(t, c, r):
    return sgc.sg(t, c, r, sha256_bytes(canonical_json(t)), sha256_bytes(canonical_json(c)),
                  sha256_bytes(canonical_json(r)))


def refused(fn, match=""):
    try:
        fn()
    except Refusal as exc:
        return match in str(exc), str(exc)[:110]
    except Exception as exc:  # noqa: BLE001 - a binding check that raises another type is reported as such
        return False, f"raised {type(exc).__name__} (not a Refusal): {str(exc)[:80]}"
    return False, "accepted"


def main(scratch: Path) -> int:
    t, c, r, ts = docs("plan_a", 501, fail={"S1": ("concentrated", 0.08, 0.95, 0.05, False)})
    inp = validate(t)
    coh.check(c, inp, ts)
    note("unedited counts pass", True)
    # (1) bindings
    t2, c2, r2, ts2 = docs("plan_a", 502, fail={"S1": ("concentrated", 0.08, 0.95, 0.05, False)})
    forged = copy.deepcopy(c2)
    forged["input_sha256"] = ts                         # another world's counts, relabelled with this sha
    ok, msg = refused(lambda: coh.check(forged, inp, ts), "u + u_fail is not")
    note("another world's counts with a forged input_sha256 are refused", ok, msg)
    cases = {
        "a count of 10**20": lambda d: d["cells"]["S1"]["1102"]["n"].__setitem__(5, 10 ** 20),
        "-0.0 as a count": lambda d: d["cells"]["S1"]["1102"]["u"].__setitem__(5, -0.0),
        "a seed key ' 1102'": lambda d: d["cells"]["S1"].update({" 1102": d["cells"]["S1"].pop("1102")}),
        "the plan_b reading": lambda d: d.update(reading="plan_b"),
        "cells as a list": lambda d: d.update(cells=[]),
        "a cell as a list": lambda d: d["cells"]["S1"].update({"1102": [1, 2, 3]}),
        "a vector of 201": lambda d: d["cells"]["S1"]["1102"]["u_fail"].append(0),
        "items 200 as a string": lambda d: d.update(items="200"),
        "kind with a trailing space": lambda d: d.update(kind=coh.KIND + " "),
        "a counts vector reversed (P = 200)": lambda d: [d["cells"]["S4"]["1105"][k].reverse() for k in ("n", "u", "u_fail")],
        "the counts of S1 1102 and 1103 swapped": lambda d: d["cells"]["S1"].update(
            {"1102": d["cells"]["S1"]["1103"], "1103": d["cells"]["S1"]["1102"]}),
        "u moved to u_fail on a prompt with n = 3 (u_fail above 3 - n)": lambda d: _u_to_fail(d),
    }
    for name, edit in cases.items():
        bad = copy.deepcopy(c)
        edit(bad)
        ok, msg = refused(lambda: coh.check(bad, inp, ts))
        note(f"refused: {name}", ok, msg)
    # duplicate keys and the command line
    paths = {k: scratch / f"{k}.json" for k in ("tables", "counts", "reading")}
    paths["tables"].write_bytes(canonical_json(t))
    paths["counts"].write_bytes(canonical_json(c))
    paths["reading"].write_bytes(canonical_json(r))
    out = scratch / "sg.json"
    rc = sgc.main(["--tables", str(paths["tables"]), "--counts", str(paths["counts"]), "--reading",
                   str(paths["reading"]), "--out", str(out)])
    note("the command line writes the file (exit 0)", rc == 0 and out.is_file(), f"exit {rc}")
    text = out.read_bytes()
    note("the output is canonical strict JSON", canonical_json(strict_json(text)) == text)
    dup = scratch / "counts-dup.json"
    raw = canonical_json(c).decode()
    dup.write_text(raw.replace('"items": 200,', '"items": 200,\n  "items": 200,', 1))
    out2 = scratch / "sg2.json"
    rc = sgc.main(["--tables", str(paths["tables"]), "--counts", str(dup), "--reading", str(paths["reading"]), "--out",
                   str(out2)])
    note("a counts file with a repeated key is refused (exit 2, nothing written)", rc == 2 and not out2.exists(),
         f"exit {rc}")
    other_r = scratch / "reading-other.json"
    other_r.write_bytes(canonical_json(r2))
    rc = sgc.main(["--tables", str(paths["tables"]), "--counts", str(paths["counts"]), "--reading", str(other_r),
                   "--out", str(out2)])
    note("B16's output of another world is refused (exit 2, nothing written)", rc == 2 and not out2.exists(), f"exit {rc}")
    rv = copy.deepcopy(r)
    rv["version"] = 2
    ok, msg = refused(lambda: run_sg(t, c, rv), "not B16's version-1")
    note("refused: B16 output version 2", ok, msg)
    # (3) the stated limit: two prompts with equal Unsafe counts but other splits swap places; a Safe failure moves
    base = run_sg(t, c, r)
    sw = copy.deepcopy(c)
    cell = sw["cells"]["S1"]["1104"]
    tot = [a + b for a, b in zip(cell["u"], cell["u_fail"])]
    pair = next(((i, k) for i in range(200) for k in range(i + 1, 200) if tot[i] == tot[k] and
                 (cell["n"][i], cell["u"][i]) != (cell["n"][k], cell["u"][k])), None)
    if pair:
        i, k = pair
        for key in ("n", "u", "u_fail"):
            cell[key][i], cell[key][k] = cell[key][k], cell[key][i]
        coh.check(sw, inp, ts)
        alt = run_sg(t, sw, r)
        d_est = max(abs(alt["coherent"]["contrasts"][n]["estimate"]["est"] - base["coherent"]["contrasts"][n]["estimate"]["est"])
                    for n in ("P4", "P5", "P6"))
        d_iv = max(abs(alt["coherent"]["contrasts"][n]["estimate"]["item_var"] - base["coherent"]["contrasts"][n]["estimate"]["item_var"])
                   for n in ("P4", "P5", "P6"))
        same_words = all(alt["coherent"]["contrasts"][n]["u_part_words"] == base["coherent"]["contrasts"][n]["u_part_words"]
                         for n in ("P4", "P5", "P6"))
        note("limit (stated): a swap of two prompts with equal Unsafe counts and other splits passes", True,
             f"prompts {pair}; max change in est {d_est:.2e} pp, in item_var {d_iv:.2e} pp^2; words same {same_words}")
    # (4) extreme but legal counts never stop the S-G reading
    extreme = {
        "every cell empty": dict(empty={(a, j) for a in gen2.MU for j in range(1101, 1108)}),
        "the full cluster empty but a0": dict(empty={(a, j) for a in ("S1", "S3", "S4") for j in range(1101, 1108)}),
        "one coherent answer per S1 cell": dict(fail={"S1": ("independent", 0.9985)}),
        "two coherent answers per A1 cell": dict(fail={"A1": ("independent", 0.997)}),
        "S1 and S4 at 99% failing (plan B)": dict(fail={"S1": ("independent", 0.99), "S4": ("independent", 0.99)}),
    }
    for name, kw in extreme.items():
        reading = "plan_b" if "plan B" in name else "plan_a"
        try:
            te, ce, re_, _ = docs(reading, 600 + len(name), **kw)
        except Refusal as exc:
            note(f"never stops: {name}", True, f"(B16 itself refuses this world: {str(exc)[:80]})")
            continue
        try:
            o = run_sg(te, ce, re_)
            blocks = [o["coherent"]["contrasts"], o["g3a"]["against_better"]["contrasts"],
                      o["g3a"]["against_worse"]["contrasts"]]
            okk = all((k["computable"] and 0.0 <= k["p_in_phi"] <= 1.0) or
                      (not k["computable"] and k["p_in_phi"] == 1.0 and k["reason"].startswith("not computable"))
                      for b in blocks for k in b.values())
            text = canonical_json(o)
            okj = canonical_json(strict_json(text)) == text
            ncs = {k: v["reason"][:70] for k, v in o["coherent"]["contrasts"].items() if not v["computable"]}
            note(f"never stops: {name}", okk and okj, f"not computable {ncs}; fits not computable "
                 f"{o['coherent']['fits_not_computable']}")
        except Exception as exc:  # noqa: BLE001
            note(f"never stops: {name}", False, f"raised {type(exc).__name__}: {str(exc)[:150]}")
    fails = [n for n, ok, _ in results if not ok]
    print(f"{len(results)} probes, {len(fails)} failed: {fails}")
    return 1 if fails else 0


def _u_to_fail(d):
    cell = d["cells"]["S3"]["1103"]
    k = next(i for i in range(200) if cell["u"][i] > 0 and cell["n"][i] == 3)
    cell["u"][k] -= 1
    cell["u_fail"][k] += 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
