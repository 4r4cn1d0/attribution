"""Second fix round's mutation harness (the re-verifier's harness, mutate_rv.py, with this round's mutants). A scratch
root MUT reaches the engine, research, tmp and the committed .ai/inputs folders of ws-c by symlink; scripts/scale78b and
the Llama sealed-set folder are COPIED (SEAL and the anchor folder too: the sealed MANIFEST records the frozen builder's
path relative to REPO, and rglob does not follow symlinked folders) and one mutant (one or more replacements) is
applied; the same pytest command runs on the baseline and on each mutant. KILLED = pytest exit non-zero AND named
failed tests AND no errors. Prints summaries and test names only."""
import pathlib
import shutil
import subprocess
import sys

S = pathlib.Path(__file__).resolve().parent
MUT = S / "mut-fix2"
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
NR = "scripts/scale78b/noise_reading.py"
MK = "scripts/scale78b/make_recipe_s78.py"
BS = ".ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py"
BR = "scripts/scale78b/build_r_draws_78b.py"
BH = "scripts/scale78b/build_h1_llama3.py"
IDENTITY = ("            if target.exists() and any(os.path.samefile(p, target) for p in (anchor, *anchor.parents)):\n"
            "                raise {r}(f\"refusing to write under {{forbidden}}\")\n")
MUTANTS = [
    # ---- RV-1: the identity comparison removed (the string comparison stays: round 2's guard before this fix)
    ("RV-1a sealed wrapper: identity check removed", "B", [(BS, IDENTITY.format(r="Refusal"), "")]),
    ("RV-1b r-draws: identity check removed", "B", [(BR, IDENTITY.format(r="Refusal"), "")]),
    ("RV-1c H1: identity check removed", "B", [(BH, IDENTITY.format(r="s1.Refusal"), "")]),
    # ---- RV-2: the re-verifier's eight (its exact replacements)
    ("C-D3b anchor_records accepts an incomplete or foreign-kind record", "maker",
     [(MK, '        if not isinstance(doc, dict) or doc.get("kind") != ANCHOR_RECORD_KIND or doc.get("complete") is not True:',
       '        if not isinstance(doc, dict):')]),
    ("C-D4b duplicate check keyed by path, not by COMPLETE.json SHA-256", "noise",
     [(NR, '            key = entry.get("complete_sha256") if isinstance(entry, dict) else None',
       '            key = entry.get("path") if isinstance(entry, dict) else None'),
      (NR, '            seen[u["complete_sha256"]] = u["where"]', '            seen[str(u["folder"])] = u["where"]')]),
    ("R2 r_edit_matches without the edit_kind check", "noise",
     [(NR, '    return doc.get("kind") == "safety-selection edit" and doc.get("edit_kind") == "remove" \\',
       '    return doc.get("kind") == "safety-selection edit" \\')]),
    ("R3 read_unit: edit.json no longer bound to the named arm's hash", "noise",
     [(NR, '        if not edit.is_file() or sha256_file(edit) != arm[len("edit-"):]:', '        if not edit.is_file():')]),
    ("R4 environment reference is a0@1102, not a0-1101", "noise",
     [(NR, '    reference = units[("a0", SEEDS[0])]', '    reference = units[("a0", SEEDS[1])]')]),
    ("R5 hex64 accepts upper-case hex", "noise",
     [(NR, 're.fullmatch(r"[0-9a-f]{64}", value)', 're.fullmatch(r"[0-9a-fA-F]{64}", value)')]),
    ("G1 r-draws guard: the absent-or-empty refusal removed", "B",
     [(BR, '    if out.exists() and any(out.iterdir()):\n        raise Refusal(f"{out} exists and is not empty: a sealed build never overwrites")\n',
       '    return None\n')]),
    ("G3 H1 CLI passes repo=None to the guard (--repo's own sealed folders unguarded)", "B",
     [(BH, "        guard_out(out, repo)\n", "        guard_out(out, None)\n")]),
]
# the behaviour test each mutant must fail (besides any committed-out hash test, which a B mutant fails as well)
EXPECTED = {
    "RV-1a": "test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder",
    "RV-1b": "test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder",
    "RV-1c": "test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder",
    "C-D3b": "test_anchor_records_skips_an_incomplete_or_foreign_record",
    "C-D4b": "test_a_copied_unit_at_another_path_with_the_same_complete_json_refuses_as_a_duplicate",
    "R2": "test_the_edit_provenance_check_refuses_a_rewrite_or_add_edit_and_a_wrong_kind",
    "R3": "test_an_r_unit_whose_edit_file_hashes_to_another_arm_refuses",
    "R4": "test_an_environment_difference_on_a0_1102_alone_is_attributed_to_it_against_the_a0_1101_reference",
    "R5": "test_hex64_accepts_sixty_four_lower_case_hex_digits_only",
    "G1": "test_the_r_draws_guard_refuses_a_folder_that_exists_and_is_not_empty",
    "G3": "test_the_h1_cli_refuses_an_output_under_the_given_repos_own_sealed_folders",
}


def setup(mutation=None):
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


def run(target):
    py, paths = TARGETS[target]
    r = subprocess.run([py, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(S / "mut-tmp")]
                       + [str(MUT / p) for p in paths], cwd=str(MUT), capture_output=True, text=True, env=ENV)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    summary = lines[-1] if lines else ""
    failed = sorted({l.split("::")[-1].split(" - ")[0] for l in lines if l.startswith("FAILED ")})
    errors = [l for l in lines if l.startswith("ERROR ")]
    kinds = sorted({("DID NOT RAISE" if "DID NOT RAISE" in l else "assert" if l.startswith("E       assert") or "AssertionError" in l
                     else "regex" if "Regex pattern" in l or "does not match" in l else None) for l in lines} - {None})
    return r.returncode, summary, failed, errors, kinds


setup()
for target in TARGETS:
    code, summary, failed, errors, kinds = run(target)
    print(f"BASELINE {target}: exit {code} | {summary} | failed {failed} | errors {len(errors)}")
    assert code == 0 and not failed and not errors, f"baseline {target} must pass"
all_ok = True
for label, target, reps in MUTANTS:
    setup((label, target, reps))
    code, summary, failed, errors, kinds = run(target)
    verdict = "KILLED" if (code != 0 and failed and not errors) else ("INVALID (errors)" if errors else "SURVIVED")
    want = EXPECTED[label.split()[0]]
    by_its_test = want in failed
    all_ok = all_ok and verdict == "KILLED" and by_its_test
    print(f"{label}: {verdict} | by its own test: {by_its_test} | {summary} | failed: {failed} | kinds: {kinds}")
print("ALL MUTANTS KILLED BY THEIR OWN TEST:", all_ok)
shutil.rmtree(MUT)
shutil.rmtree(S / "mut-tmp", ignore_errors=True)
