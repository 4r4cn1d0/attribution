"""Re-verifier (round 2) mutation harness: MY OWN mutants of the RV-1 identity block and of the eight RV-2 checks,
with their own replacement text (not the fixer's). A scratch root MUT reaches the engine, research, tmp and the
committed .ai/inputs folders of ws-c by symlink; scripts/scale78b, the Llama sealed-set folder, SEAL and the anchor
folder are COPIED and one mutant is applied; the same pytest command runs on the baseline and on each mutant.
KILLED = pytest exit non-zero AND named failed tests AND no errors; OWN = the test written for the gap is among the
failures. Prints summaries and test names only. Usage: python -I -B mutate_rv2.py <ws-c>"""
import pathlib, shutil, subprocess, sys
S = pathlib.Path(__file__).resolve().parent
MUT = S / "mut-rv2"
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
T_CASE = "test_the_guard_refuses_a_case_variant_spelling_of_a_sealed_folder"
T_SYM = "test_the_guard_refuses_a_symlink_a_dotted_and_a_relative_path_into_a_sealed_folder"
WALK = "    while not anchor.exists() and anchor.parent != anchor:\n        anchor = anchor.parent\n"
IDENT = "            if target.exists() and any(os.path.samefile(p, target) for p in (anchor, *anchor.parents)):\n"
# (label, target, [(file, old, new)], own test(s) expected among the failures)
MUTANTS = [
    ("RV1-x1 sealed: identity checks the anchor only, not its parents", "B",
     [(BS, "for p in (anchor, *anchor.parents))", "for p in (anchor,))")], [T_CASE]),
    ("RV1-x2 r-draws: identity by string equality instead of samefile", "B",
     [(BR, "any(os.path.samefile(p, target) for p in", "any(p == target for p in")], [T_CASE]),
    ("RV1-x3 H1: no ancestor walk (anchor = out, which may not exist)", "B",
     [(BH, WALK, "")], [T_CASE, T_SYM]),
    ("RV1-x4 sealed: the identity refusal dropped (string comparison only)", "B",
     [(BS, IDENT, "            if False:\n")], [T_CASE]),
    ("C-D3b-a maker: anchor_records keeps an incomplete record (only the complete check dropped)", "maker",
     [(MK, ' or doc.get("complete") is not True:', ":")], ["test_anchor_records_skips_an_incomplete_or_foreign_record"]),
    ("C-D3b-b maker: anchor_records keeps a foreign-kind record (only the kind check dropped)", "maker",
     [(MK, 'doc.get("kind") != ANCHOR_RECORD_KIND or ', "")], ["test_anchor_records_skips_an_incomplete_or_foreign_record"]),
    ("C-D4b-a noise: the pre-read duplicate refusal never fires", "noise",
     [(NR, "            if key is not None and key in seen:\n", "            if False:\n")],
     ["test_a_copied_unit_at_another_path_with_the_same_complete_json_refuses_as_a_duplicate"]),
    ("C-D4b-b noise: duplicate key is the path (the fixer's mutant, replicated)", "noise",
     [(NR, '            key = entry.get("complete_sha256") if isinstance(entry, dict) else None', '            key = entry.get("path") if isinstance(entry, dict) else None'),
      (NR, '            seen[u["complete_sha256"]] = u["where"]', '            seen[str(u["folder"])] = u["where"]')],
     ["test_a_copied_unit_at_another_path_with_the_same_complete_json_refuses_as_a_duplicate"]),
    ("R2 noise: edit_kind only has to be present", "noise",
     [(NR, 'doc.get("edit_kind") == "remove"', 'doc.get("edit_kind") is not None')],
     ["test_the_edit_provenance_check_refuses_a_rewrite_or_add_edit_and_a_wrong_kind"]),
    ("R3 noise: edit.json's hash compared with itself (binding to the arm dropped)", "noise",
     [(NR, 'sha256_file(edit) != arm[len("edit-"):]', "sha256_file(edit) != sha256_file(edit)")],
     ["test_an_r_unit_whose_edit_file_hashes_to_another_arm_refuses"]),
    ("R4-a noise: environment reference is a0@1103 (not 1101, not 1102)", "noise",
     [(NR, '    reference = units[("a0", SEEDS[0])]', '    reference = units[("a0", SEEDS[2])]')],
     ["test_an_environment_difference_on_a0_1102_alone_is_attributed_to_it_against_the_a0_1101_reference"]),
    ("R4-b noise: environment reference is R@1101", "noise",
     [(NR, '    reference = units[("a0", SEEDS[0])]', '    reference = units[("R", SEEDS[0])]')],
     ["test_an_environment_difference_on_a0_1102_alone_is_attributed_to_it_against_the_a0_1101_reference"]),
    ("R5-a noise: hex64 lower-cases before matching", "noise",
     [(NR, 're.fullmatch(r"[0-9a-f]{64}", value)', 're.fullmatch(r"[0-9a-f]{64}", value.lower())')],
     ["test_hex64_accepts_sixty_four_lower_case_hex_digits_only"]),
    ("R5-b noise: hex64 accepts 63 to 65 digits", "noise",
     [(NR, 'r"[0-9a-f]{64}"', 'r"[0-9a-f]{63,65}"')],
     ["test_hex64_accepts_sixty_four_lower_case_hex_digits_only"]),
    ("G1-a r-draws: non-empty means two or more entries", "B",
     [(BR, "    if out.exists() and any(out.iterdir()):", "    if out.exists() and len(list(out.iterdir())) > 1:")],
     ["test_the_r_draws_guard_refuses_a_folder_that_exists_and_is_not_empty"]),
    ("G3-a H1: the CLI guards with REPO, ignoring --repo", "B",
     [(BH, "        guard_out(out, repo)\n", "        guard_out(out, REPO)\n")],
     ["test_the_h1_cli_refuses_an_output_under_the_given_repos_own_sealed_folders"]),
]


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
        if entry.name in ("scale-78b-sealed-llama3-20261105", "gate-b-anchors-20261008", "gate-b-sealed-20261008"):
            shutil.copytree(entry, MUT / ".ai/inputs" / entry.name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            (MUT / ".ai/inputs" / entry.name).symlink_to(entry)
    shutil.copytree(WS / "scripts/scale78b", MUT / "scripts/scale78b", ignore=shutil.ignore_patterns("__pycache__"))
    if mutation is not None:
        label, _, reps, _ = mutation
        for rel, old, new in reps:
            path = MUT / rel
            text = path.read_text(encoding="utf-8")
            assert text.count(old) == 1, f"{label}: anchor in {rel} found {text.count(old)} times"
            path.write_text(text.replace(old, new), encoding="utf-8")


def run(target):
    py, paths = TARGETS[target]
    r = subprocess.run([py, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(S / "mut-tmp")] + [str(MUT / p) for p in paths],
                       cwd=str(MUT), capture_output=True, text=True, env=ENV)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.strip()]
    summary = lines[-1] if lines else ""
    failed = sorted({l.split("::")[-1].split(" - ")[0] for l in lines if l.startswith("FAILED ")})
    errors = [l for l in lines if l.startswith("ERROR ")]
    kinds = sorted({("DID NOT RAISE" if "DID NOT RAISE" in l else "assert" if l.startswith("E       assert") or "AssertionError" in l
                     else "regex" if "Regex pattern" in l or "does not match" in l
                     else "exception" if l.startswith("E       ") and "Error" in l else None) for l in lines} - {None})
    return r.returncode, summary, failed, errors, kinds


setup()
for target in TARGETS:
    code, summary, failed, errors, kinds = run(target)
    print(f"BASELINE {target}: exit {code} | {summary} | failed {failed} | errors {len(errors)}")
    assert code == 0 and not failed and not errors, f"baseline {target} must pass"
all_own = True
survivors = []
for label, target, reps, own in MUTANTS:
    setup((label, target, reps, own))
    code, summary, failed, errors, kinds = run(target)
    verdict = "KILLED" if (code != 0 and failed and not errors) else ("INVALID (errors)" if errors else "SURVIVED")
    by_own = verdict == "KILLED" and any(t in failed for t in own)
    if verdict != "KILLED":
        survivors.append(label)
    all_own = all_own and by_own
    print(f"{label}: {verdict}{' by its own test' if by_own else ''} | {summary} | failed: {failed} | kinds: {kinds}")
print(f"SURVIVORS: {survivors}")
print(f"ALL MUTANTS KILLED BY THEIR OWN TEST: {all_own}")
shutil.rmtree(MUT)
shutil.rmtree(S / "mut-tmp", ignore_errors=True)
