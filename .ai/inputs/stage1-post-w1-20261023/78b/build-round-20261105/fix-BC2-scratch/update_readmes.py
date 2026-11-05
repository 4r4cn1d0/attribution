"""The three READMEs after the second rebuild: the new hashes (with the earlier builds as history), the identity guard,
the test counts, and RV-3's sentence (the engine tests use id-only engine_stub() views, never load_prepared). Exact
anchors, each found once. Prints the files changed only."""
import pathlib
import sys

WS = pathlib.Path(sys.argv[1])
SEALED = WS / ".ai/inputs/scale-78b-sealed-llama3-20261105/README.md"
RDRAWS = WS / ".ai/inputs/scale-78b-r-draws-olmo2-20261105/README.md"
H1 = WS / ".ai/inputs/scale-78b-length-rules-llama3-20261105/README.md"

EDITS = {
    SEALED: [
        ("# The Llama sealed set (built 2026-11-05 13:48 UTC; the 7-8B tier's T3 and stage 2's Llama files)",
         "# The Llama sealed set (first built 2026-11-05 13:48 UTC; this build 16:04 UTC; the 7-8B tier's T3 and stage 2's Llama files)"),
        ("`out/MANIFEST.json` (`ba524373…`, every file's SHA-256 and arm). Built on the Mac by `build_sealed_llama3.py`\n"
         "(SHA-256 `227aed4f…`; rebuilt into an empty `out/` in the fix round of 5 Nov 2026 after the write guard was widened to\n"
         "SEAL, the anchor list and stage 1's folder, resolved from the script's own checkout, B-M2/B-M3; the round-1 build,\n"
         "wrapper `5cd45926…` and MANIFEST `76415c42…`, was removed first) on the frozen builder BLD `build_sealed.py`\n"
         "(`80cb8944…`, never copied or edited) with engine\n"
         "identity `472fc7f6…`. $0; no pod, no network.\n",
         "`out/MANIFEST.json` (`2a1db220…`, every file's SHA-256 and arm). Built on the Mac by `build_sealed_llama3.py`\n"
         "(SHA-256 `1ca6cdb4…`) on the frozen builder BLD `build_sealed.py` (`80cb8944…`, never copied or edited) with engine\n"
         "identity `472fc7f6…`. $0; no pod, no network. Rebuilt twice into an empty `out/` on 5 Nov 2026, before the first\n"
         "commit: in the fix round, after the write guard was widened to SEAL, the anchor list and stage 1's folder, resolved\n"
         "from the script's own checkout (B-M2/B-M3; wrapper `227aed4f…`, MANIFEST `ba524373…`), and in the second fix round,\n"
         "after the guard was made to compare folders by directory identity (RV-1; this build). The round-1 build (wrapper\n"
         "`5cd45926…`, MANIFEST `76415c42…`) and the fix-round build were each removed first. The remove lists come from BLD's\n"
         "draws and do not depend on the wrapper's bytes; d = 1-10 are checked against SEAL and stage 1 at every build.\n"),
        ("refused against the OLMo set. The wrapper never writes under SEAL or under `.ai/inputs/stage1-commitments-20261016/`.\n",
         "refused against the OLMo set. The wrapper never writes under SEAL, the anchor list or\n"
         "`.ai/inputs/stage1-commitments-20261016/`: the guard compares the resolved paths and, for each of those folders that\n"
         "exists, directory identity (`os.path.samefile` on the deepest existing ancestor of `--out` and its parents), so a\n"
         "case-variant spelling on this Mac's case-insensitive disk, a symlink and a dotted or relative path refuse too (RV-1).\n"),
        ("**Tests** (`tests/test_build_sealed_llama3.py`, 15 tests;", "**Tests** (`tests/test_build_sealed_llama3.py`, 17 tests;"),
        ("(d) the engine's `parse_edit`\n"
         "accepts each Llama file against the Llama set (the engine's own `load_prepared`) and refuses it against the OLMo set;\n",
         "(d) the engine's `parse_edit`\n"
         "accepts each Llama file against the Llama set and refuses it against the OLMo set, on id-only `engine_stub()` views of\n"
         "both sets (never the engine's `load_prepared`, which reads prompt text);\n"),
        ("a changed BLD refuses; a tampered SEAL file refuses; writing under SEAL or stage 1's folder refuses; 75 rows per unit\n"
         "in every R file; the 16 draws are distinct.\n",
         "a changed BLD refuses; a tampered SEAL file refuses; writing under SEAL, the anchor list or stage 1's folder refuses,\n"
         "by path string and by directory identity (a case-variant spelling, a symlink, a dotted and a relative path, on a fake\n"
         "checkout layout under the test's temporary folder); 75 rows per unit in every R file; the 16 draws are distinct.\n"),
    ],
    RDRAWS: [
        ("# OLMo random-removal draws d = 11-16 (built 2026-11-05 13:50 UTC; the 12-seed branch H (b))",
         "# OLMo random-removal draws d = 11-16 (first built 2026-11-05 13:50 UTC; this build 16:04 UTC; the 12-seed branch H (b))"),
        ("and `out/MANIFEST.json` (`189275c0…`). Built on the Mac by `scripts/scale78b/build_r_draws_78b.py` (SHA-256\n"
         "`5cd1036d…`; rebuilt into an empty `out/` in the fix round of 5 Nov 2026 after the write guard was widened to SEAL, the\n"
         "anchor list and stage 1's folder, resolved from the script's own checkout, B-M3; the round-1 build, script `25dd7aca…`\n"
         "and MANIFEST `da634837…`, was removed first) on the frozen builder BLD `build_sealed.py` (`80cb8944…`, loaded by path\n"
         "after its SHA-256 check, never\n"
         "copied or edited), engine identity `472fc7f6…`. $0.\n",
         "and `out/MANIFEST.json` (`22858dbf…`). Built on the Mac by `scripts/scale78b/build_r_draws_78b.py` (SHA-256\n"
         "`18f2fec8…`) on the frozen builder BLD `build_sealed.py` (`80cb8944…`, loaded by path after its SHA-256 check, never\n"
         "copied or edited), engine identity `472fc7f6…`. $0. Rebuilt twice into an empty `out/` on 5 Nov 2026, before the\n"
         "first commit: in the fix round, after the write guard was widened to SEAL, the anchor list and stage 1's folder,\n"
         "resolved from the script's own checkout (B-M3; script `5cd1036d…`, MANIFEST `189275c0…`), and in the second fix round,\n"
         "after the guard was made to compare folders by directory identity (RV-1; this build). The round-1 build (script\n"
         "`25dd7aca…`, MANIFEST `da634837…`) and the fix-round build were each removed first. The remove lists come from BLD's\n"
         "draws and do not depend on the script's bytes.\n"),
        ("so a re-run gives the same bytes. The script never writes under SEAL or under stage 1's folder.\n",
         "so a re-run gives the same bytes. The script never writes under SEAL, the anchor list or stage 1's folder: the guard\n"
         "compares the resolved paths and, for each of those folders that exists, directory identity (`os.path.samefile` on the\n"
         "deepest existing ancestor of `--out` and its parents), so a case-variant spelling on a case-insensitive disk, a symlink\n"
         "and a dotted or relative path refuse too (RV-1); an output folder that exists and is not empty refuses.\n"),
        ("**Tests** (`scripts/scale78b/tests/test_build_r_draws_78b.py`, 6 tests;", "**Tests** (`scripts/scale78b/tests/test_build_r_draws_78b.py`, 9 tests;"),
        ("re-run gives the same bytes; the committed `out/` equals a fresh build; a tampered SEAL file, a changed BLD and a write\n"
         "under SEAL or stage 1's folder refuse.\n",
         "re-run gives the same bytes; the committed `out/` equals a fresh build; a tampered SEAL file, a changed BLD, a write\n"
         "under SEAL or stage 1's folder (by path string and by directory identity: a case-variant spelling, a symlink, a dotted\n"
         "and a relative path, on a fake checkout layout) and a non-empty output folder refuse.\n"),
    ],
    H1: [
        ("# H1 on the Llama manifest (built 2026-11-05 13:52 UTC; shared by the 7-8B tier and stage 2)",
         "# H1 on the Llama manifest (first built 2026-11-05 13:52 UTC; this build 16:04 UTC; shared by the 7-8B tier and stage 2)"),
        ("**What.** `out/edits/octile_0.json` (`9204121a…`): H1,", "**What.** `out/edits/octile_0.json` (`9a01637e…`): H1,"),
        ("`out/MANIFEST.json` (`29347da2…`). Built on the Mac by `scripts/scale78b/build_h1_llama3.py` (SHA-256 `504e9462…`;\n"
         "rebuilt into an empty `out/` in the fix round of 5 Nov 2026 after the write guard was widened to SEAL, the anchor list\n"
         "and stage 1's folder, resolved from the script's own checkout, B-M2/B-M3; the round-1 build, script `8b00a67b…`,\n"
         "`octile_0.json` `fdd35004…` and MANIFEST `189cd139…`, was removed first; the remove list is unchanged),\n"
         "engine identity `472fc7f6…`. $0.",
         "`out/MANIFEST.json` (`24c1305a…`). Built on the Mac by `scripts/scale78b/build_h1_llama3.py` (SHA-256 `26f2f2a1…`),\n"
         "engine identity `472fc7f6…`. $0. Rebuilt twice into an empty `out/` on 5 Nov 2026, before the first commit: in the\n"
         "fix round, after the write guard was widened to SEAL, the anchor list and stage 1's folder, resolved from the script's\n"
         "own checkout (B-M2/B-M3; script `504e9462…`, `octile_0.json` `9204121a…`, MANIFEST `29347da2…`), and in the second fix\n"
         "round, after the guard was made to compare folders by directory identity (RV-1; this build). The round-1 build (script\n"
         "`8b00a67b…`, `octile_0.json` `fdd35004…`, MANIFEST `189cd139…`) and the fix-round build were each removed first; the\n"
         "remove list is unchanged (the same cut points and by-category counts at every build)."),
        ("**Tests** (`scripts/scale78b/tests/test_build_h1_llama3.py`, 6 tests;", "**Tests** (`scripts/scale78b/tests/test_build_h1_llama3.py`, 9 tests;"),
        ("the same bytes and the committed `out/` equals a fresh build; a wrong manifest pin refuses.\n",
         "the same bytes and the committed `out/` equals a fresh build; a wrong manifest pin refuses; the write guard refuses SEAL,\n"
         "the anchor list and stage 1's folder of this checkout and of `--repo`, by path string and by directory identity (a\n"
         "case-variant spelling, a symlink, a dotted and a relative path, on a fake checkout layout), through the guard and\n"
         "through the CLI.\n"),
    ],
}
for path, reps in EDITS.items():
    text = path.read_text(encoding="utf-8")
    for old, new in reps:
        assert text.count(old) == 1, f"{path.parent.name}/README.md: anchor found {text.count(old)} times:\n{old[:120]}"
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print(f"updated {path.relative_to(WS)}")
