"""The verifier's own near mutants (not in the builder's spec), run against the builder's new tests only (a probe of
test gaps, not the spec runner): each mutant edits a copy of scripts/stage1_s1 and the named test files run with -x.
KILLED = exit 1 with a failure; SURVIVED = exit 0.

    python -B my_mutants.py <ws> <scratch> [ids]
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SG, COH = "sg_coherent.py", "coherent.py"
T_SG, T_COH = "test_sg_coherent.py", "test_coherent.py"
MUTANTS = {
    "V1-fam-sides-6": (SG, "    fam_level = 1.0 - 2.0 * float(alpha()) / dsg.familywise_sides\n",
                       "    fam_level = 1.0 - 2.0 * float(alpha()) / 6\n", [T_SG]),
    "V2-headline-O-L-swapped": (SG, "head = labels.headline(u, (\"O\", name) in rejected, (\"L\", name) in rejected)",
                                "head = labels.headline(u, (\"L\", name) in rejected, (\"O\", name) in rejected)", [T_SG]),
    "V3-ci90-is-familywise": (SG, "e.est, e.interval(level), e.interval(fam_level), delta)",
                              "e.est, e.interval(fam_level), e.interval(fam_level), delta)", [T_SG]),
    "V4-planB-a0-in-fit": (SG, "members = tuple(a for a in dsg.cluster_arms(cluster) if",
                           "members = tuple(a for a in dsg.arms if dsg.cluster[a] == cluster and", [T_SG]),
    "V5-paired-no-item-part": (SG, "e = con.contrast_paired(table, c, m, seeds, scale, True, name,",
                               "e = con.contrast_paired(table, c, m, seeds, scale, False, name,", [T_SG]),
    "V6-identity-tolerance-1": (COH, "(u + u_fail)) <= 1e-9):", "(u + u_fail)) <= 1.0):", [T_COH]),
    "V7-x-items-minus-1": (SG, "    num = big_u * big_n + items * (u.astype(np.int64)",
                           "    num = big_u * big_n + (items - 1) * (u.astype(np.int64)", [T_SG]),
    "V8-corner-cache-by-cluster": (SG, "            if (cluster, arm) not in cache:              # P1-P3 share R's \"against worse\" table: one fit\n"
                                       "                table = corner_table(inp.tables[\"U\"], g3, arm)\n"
                                       "                cache[(cluster, arm)] = (table, *cluster_fits(table, dsg, scale, floor, cfg, clusters=(cluster,)))\n"
                                       "            table, fits, reasons = cache[(cluster, arm)]\n",
                                   "            if cluster not in cache:\n"
                                   "                table = corner_table(inp.tables[\"U\"], g3, arm)\n"
                                   "                cache[cluster] = (table, *cluster_fits(table, dsg, scale, floor, cfg, clusters=(cluster,)))\n"
                                   "            table, fits, reasons = cache[cluster]\n",
                                   [T_SG]),
    "V9-paired-on-common-count-df": (SG, "e = con.contrast_paired(table, c, m, seeds, scale, True, name,",
                                     "e = con.contrast_paired(table, c, m, seeds[:-1] if len(seeds) > 2 else seeds, scale, True, name,",
                                     [T_SG]),
    "V10-differs-words-only": (SG, "\"differs_from_primary\": words_differ or head_differs}",
                               "\"differs_from_primary\": words_differ}", [T_SG]),
}


def main():
    ws, scratch = Path(sys.argv[1]), Path(sys.argv[2])
    ids = sys.argv[3].split(",") if len(sys.argv) > 3 else list(MUTANTS)
    py = sys.executable
    for mid in ids:
        f, find, repl, tests = MUTANTS[mid]
        folder = scratch / mid
        shutil.rmtree(folder, ignore_errors=True)
        copy = folder / "copy"
        shutil.copytree(ws / "scripts/stage1_s1", copy / "scripts/stage1_s1",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        p = copy / "scripts/stage1_s1/reading_input" / f
        t = p.read_text()
        if t.count(find) != 1:
            print(f"{mid:<30} INVALID  find occurs {t.count(find)} times", flush=True)
            shutil.rmtree(folder, ignore_errors=True)
            continue
        p.write_text(t.replace(find, repl))
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": f"{copy}{os.pathsep}{ws}"}
        paths = [str(copy / "scripts/stage1_s1/reading_input/tests" / x) for x in tests]
        t0 = time.monotonic()
        r = subprocess.run([py, "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "-W", "ignore",
                            f"--basetemp={folder / 'bt'}", *paths], cwd=copy, env=env, capture_output=True, text=True,
                           timeout=590)
        lines = [x for x in r.stdout.splitlines() if x.strip()]
        last = lines[-1] if lines else r.stderr[-200:]
        failed = [x for x in lines if x.startswith("FAILED")]
        outcome = ("KILLED" if r.returncode == 1 and " failed" in last and " error" not in last
                   else "SURVIVED" if r.returncode == 0 else "INVALID")
        print(f"{mid:<30} {outcome:<8} exit {r.returncode} {time.monotonic() - t0:5.1f} s | {last[:100]} | "
              f"{failed[0][:150] if failed else ''}", flush=True)
        shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    main()
