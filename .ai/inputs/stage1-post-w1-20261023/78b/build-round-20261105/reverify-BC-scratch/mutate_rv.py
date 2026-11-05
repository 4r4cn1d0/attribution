"""Re-verifier's mutation harness (tracks B and C). A scratch root MUT reaches the engine, research, tmp and the
committed .ai/inputs folders of ws-c by symlink; scripts/scale78b and the Llama sealed-set folder are COPIED and one
mutant (one or more replacements) is applied; the same pytest command runs on the baseline and on each mutant.
KILLED = pytest exit non-zero AND named failed tests AND no errors. Prints summaries and test names only."""
import pathlib, shutil, subprocess, sys
S = pathlib.Path(__file__).resolve().parent
MUT = S / "mut-rv"
WS = pathlib.Path(sys.argv[1])
PY_SCI = "/Users/spiderishi/Coding/attribution/.venv/bin/python"
PY_MAIN = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": str(S)}
TARGETS = {
    "noise": (PY_SCI, ["scripts/scale78b/tests/test_noise_reading.py"]),
    "maker": (PY_MAIN, ["scripts/scale78b/tests/test_make_recipe_s78.py"]),
    "B": (PY_MAIN, [".ai/inputs/scale-78b-sealed-llama3-20261105/tests", "scripts/scale78b/tests/test_build_r_draws_78b.py",
                    "scripts/scale78b/tests/test_build_h1_llama3.py"]),
}
NR = "scripts/scale78b/noise_reading.py"; MK = "scripts/scale78b/make_recipe_s78.py"
BS = ".ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py"; BR = "scripts/scale78b/build_r_draws_78b.py"; BH = "scripts/scale78b/build_h1_llama3.py"
ROOTS_OLD = "    roots = [REPO.resolve()]\n    if repo is not None and repo.resolve() not in roots:\n        roots.append(repo.resolve())\n"
ROOTS_R1 = "    roots = [repo.resolve()] if repo is not None else [REPO.resolve()]\n"
MUTANTS = [
    # ---- per item
    ("B-M2 H1 guard back to the stage-1 folder only", "B", [(BH, "FORBIDDEN_DIRS = (SEAL_DIR_REL, ANCHORS_DIR_REL, STAGE1_DIR_REL)", "FORBIDDEN_DIRS = (STAGE1_DIR_REL,)")]),
    ("B-M3a sealed wrapper: forbidden roots from --repo only (round 1)", "B", [(BS, ROOTS_OLD, ROOTS_R1)]),
    ("B-M3b r-draws: forbidden roots from --repo only (round 1)", "B", [(BR, ROOTS_OLD, ROOTS_R1)]),
    ("B-M3c H1: forbidden roots from --repo only (round 1)", "B", [(BH, ROOTS_OLD, ROOTS_R1)]),
    ("C-D1a pooled median over the first family's three SEs", "noise", [(NR, "    median = GB.median_term(se2s)", "    median = GB.median_term(se2s[:3])")]),
    ("C-D1b s_arm df = 2k instead of the summed arm df", "noise", [(NR, '    df_arm = sum(e["arm_df"] for e in exact)', "    df_arm = 2 * k")]),
    ("C-D1c sigma_pool ignores the median term", "noise", [(NR, '"sigma_pool_pp": GB.sigma_value(sigma),', '"sigma_pool_pp": GB.sigma_value(((p_pool,),)),')]),
    ("C-D2a review threshold loosened by 1e-6", "noise", [(NR, "    review = not GB.ge(2 * SESOI_PP, ex(MDE_FACTOR[plan]), sigma)", "    review = not GB.ge(2 * SESOI_PP + Fraction(1, 10 ** 6), ex(MDE_FACTOR[plan]), sigma)")]),
    ("C-D2b review strict at the ceiling (gt instead of ge)", "noise", [(NR, "    review = not GB.ge(2 * SESOI_PP, ex(MDE_FACTOR[plan]), sigma)", "    review = not GB.gt(2 * SESOI_PP, ex(MDE_FACTOR[plan]), sigma)")]),
    ("C-D2c ceilings pinned to the round-1 constants", "noise", [(NR, "CEILING_SIGMA_PP = {plan: Fraction(2 * SESOI_PP) / Fraction(factor) for plan, factor in MDE_FACTOR.items()}", 'CEILING_SIGMA_PP = {"A": Fraction("7.0390"), "B9": Fraction("9.2718"), "H": Fraction("10.7062")}')]),
    ("C-D3a anchored_to ignores the record's recipe (any family's record anchors)", "maker", [(MK, '        if record["anchor_file_sha256"] == digest and record["recipe_sha256"] == MAIN[family]["config_sha256"]:', '        if record["anchor_file_sha256"] == digest:')]),
    ("C-D3b anchor_records accepts an incomplete or foreign-kind record", "maker", [(MK, '        if not isinstance(doc, dict) or doc.get("kind") != ANCHOR_RECORD_KIND or doc.get("complete") is not True:', '        if not isinstance(doc, dict):')]),
    ("C-D4a duplicate check back after read_unit (round-1 order)", "noise", [(NR,
        '            key = entry.get("complete_sha256") if isinstance(entry, dict) else None\n            if key is not None and key in seen:\n                refuse(f"{where}: its COMPLETE.json SHA-256 is already read as {seen[key]}")\n            u = read_unit(entry, role, s, name, engine[role], where, base)\n',
        '            u = read_unit(entry, role, s, name, engine[role], where, base)\n            key = u["complete_sha256"]\n            if key in seen:\n                refuse(f"{where}: its COMPLETE.json SHA-256 is already read as {seen[key]}")\n')]),
    ("C-D4b duplicate check keyed by path, not by COMPLETE.json SHA-256", "noise", [(NR, '            key = entry.get("complete_sha256") if isinstance(entry, dict) else None', '            key = entry.get("path") if isinstance(entry, dict) else None'),
                                                                                  (NR, '            seen[u["complete_sha256"]] = u["where"]', '            seen[str(u["folder"])] = u["where"]')]),
    ("C-D5a fresh-trajectory rule applied to a0 instead of R", "noise", [(NR, '    if role == "R" and job.get("resume_from") is not None:', '    if role == "a0" and job.get("resume_from") is not None:')]),
    ("C-D5b parity family refused only beside two tier families", "noise", [(NR, "    if tier and parity:", "    if len(tier) > 1 and parity:")]),
    ("A6 pooled SD(r) term from the plain reading while the fallback governs", "noise", [(NR, '"_exact": {"sdr2": rd["sdr2"],', '"_exact": {"sdr2": readings["plain"]["sdr2"],')]),
    # ---- my own
    ("R1 r_edit_matches without the manifest check", "noise", [(NR, '        and doc.get("manifest_sha256") == FAMILIES[family]["manifest_sha256"] and selection.get("family") == "R" \\', '        and selection.get("family") == "R" \\')]),
    ("R2 r_edit_matches without the edit_kind check", "noise", [(NR, '    return doc.get("kind") == "safety-selection edit" and doc.get("edit_kind") == "remove" \\', '    return doc.get("kind") == "safety-selection edit" \\')]),
    ("R3 read_unit: edit.json no longer bound to the named arm's hash", "noise", [(NR, '        if not edit.is_file() or sha256_file(edit) != arm[len("edit-"):]:', '        if not edit.is_file():')]),
    ("R4 environment reference is a0@1102, not a0-1101", "noise", [(NR, '    reference = units[("a0", SEEDS[0])]', '    reference = units[("a0", SEEDS[1])]')]),
    ("R5 hex64 accepts upper-case hex", "noise", [(NR, 're.fullmatch(r"[0-9a-f]{64}", value)', 're.fullmatch(r"[0-9a-fA-F]{64}", value)')]),
    ("R6 the environment trigger dropped (fallback on fingerprint only)", "noise", [(NR, '    fallback = environment or fingerprint == "differs"', '    fallback = fingerprint == "differs"')]),
    ("R7 pooled df = k", "noise", [(NR, '"seed_rule": seed_rule(sigma, 2 * k)}', '"seed_rule": seed_rule(sigma, k)}')]),
    ("G1 r-draws guard: the absent-or-empty refusal removed", "B", [(BR, '    if out.exists() and any(out.iterdir()):\n        raise Refusal(f"{out} exists and is not empty: a sealed build never overwrites")\n', '    return None\n')]),
    ("G2 sealed wrapper guard: equality with the forbidden folder itself not refused", "B", [(BS, "            if out == target or target in out.parents:", "            if target in out.parents:")]),
    ("G3 H1 CLI passes repo=None to the guard (--repo's own sealed folders unguarded)", "B", [(BH, "        guard_out(out, repo)\n", "        guard_out(out, None)\n")]),
    ("G4 sealed wrapper CLI: the parity folder not guarded", "B", [(BS, "            guard_out(args.olmo_parity_out, repo)\n", "            pass\n")]),
]


def setup(mutation=None, logger=False):
    if MUT.exists():
        shutil.rmtree(MUT)
    (MUT / "scripts").mkdir(parents=True)
    for name in ("gate_b_reading.py", "family_probe_reading.py", "killtest_stage0_reading.py", "stage1", "stage1_s1"):
        (MUT / "scripts" / name).symlink_to(WS / "scripts" / name)
    for name in ("experiments", "research", "tmp"):
        (MUT / name).symlink_to(WS / name)
    (MUT / ".ai/inputs").mkdir(parents=True)
    for entry in sorted((WS / ".ai/inputs").iterdir()):
        if entry.name == "scale-78b-sealed-llama3-20261105":
            shutil.copytree(entry, MUT / ".ai/inputs" / entry.name, ignore=shutil.ignore_patterns("__pycache__"))
        elif entry.name in ("gate-b-anchors-20261008", "gate-b-sealed-20261008"):
            # anchors: rglob does not follow symlinked dirs; SEAL: the sealed MANIFEST records the frozen builder's path
            # relative to REPO, and a symlink would resolve outside REPO (an absolute path: a harness artifact, M)
            shutil.copytree(entry, MUT / ".ai/inputs" / entry.name)
        else:
            (MUT / ".ai/inputs" / entry.name).symlink_to(entry)
    shutil.copytree(WS / "scripts/scale78b", MUT / "scripts/scale78b", ignore=shutil.ignore_patterns("__pycache__"))
    if mutation is not None:
        label, _, reps = mutation
        for rel, old, new in reps:
            path = MUT / rel
            text = path.read_text(encoding="utf-8")
            assert text.count(old) == 1, f"{label}: anchor in {rel} found {text.count(old)} times"
            path.write_text(text.replace(old, new), encoding="utf-8")
    if logger:
        (MUT / "conftest.py").write_text('''
import builtins, io, pathlib
LOG = pathlib.Path(%r)
_real = builtins.open
def _logged(file, *a, **k):
    s = str(file)
    if "tmp/kt-prepared" in s or "kt-prepared" in s:
        with _real(LOG, "a") as fh:
            fh.write(s.split("kt-prepared/", 1)[-1] + "\\n")
    for bad in ("query_rows.jsonl", "/hidden/", "/selector/", "/banks/", "/auditor/", "samples.jsonl", "generations.jsonl"):
        if bad in s:
            raise PermissionError("re-verifier: a text file was opened: " + s.split("/")[-1])
    return _real(file, *a, **k)
builtins.open = _logged
io.open = _logged
''' % str(S / "opened_prepared_files.log"))


def run(target):
    py, paths = TARGETS[target]
    r = subprocess.run([py, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(S / "mut-tmp")] + [str(MUT / p) for p in paths],
                       cwd=str(MUT), capture_output=True, text=True, env=ENV)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    summary = lines[-1] if lines else ""
    failed = sorted({l.split("::")[-1].split(" - ")[0] for l in lines if l.startswith("FAILED ")})
    errors = [l for l in lines if l.startswith("ERROR ")]
    kinds = sorted({("DID NOT RAISE" if "DID NOT RAISE" in l else "assert" if l.startswith("E       assert") or "AssertionError" in l
                     else "regex" if "Regex pattern" in l or "does not match" in l else None) for l in lines} - {None})
    return r.returncode, summary, failed, errors, kinds


if "--logger" in sys.argv:
    log = S / "opened_prepared_files.log"
    if log.exists():
        log.unlink()
    setup(logger=True)
    code, summary, failed, errors, kinds = run("B")
    opened = sorted(set(log.read_text().splitlines())) if log.exists() else []
    print(f"B-M1 LOGGED RUN: exit {code} | {summary} | failed {failed} | errors {len(errors)}")
    print(f"B-M1 prepared-set files opened by the B tests ({len(opened)} distinct): {opened}")
    shutil.rmtree(MUT); shutil.rmtree(S / "mut-tmp", ignore_errors=True)
    sys.exit(0)

setup()
base = {}
for target in TARGETS:
    base[target] = run(target)
    code, summary, failed, errors, kinds = base[target]
    print(f"BASELINE {target}: exit {code} | {summary} | failed {failed} | errors {len(errors)}")
    assert code == 0 and not failed and not errors, f"baseline {target} must pass"
for label, target, reps in MUTANTS:
    setup((label, target, reps))
    code, summary, failed, errors, kinds = run(target)
    verdict = "KILLED" if (code != 0 and failed and not errors) else ("INVALID (errors)" if errors else "SURVIVED")
    print(f"{label}: {verdict} | {summary} | failed: {failed} | kinds: {kinds}")
shutil.rmtree(MUT)
shutil.rmtree(S / "mut-tmp", ignore_errors=True)
