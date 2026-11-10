"""RV-1: make guard_out compare by directory identity in the three hashed build scripts of ws-c (exact-anchor
replacements; each anchor must occur exactly once; prints the files changed and their new SHA-256 only)."""
import hashlib
import pathlib
import sys

WS = pathlib.Path(sys.argv[1])
SEALED = WS / ".ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py"
RDRAWS = WS / "scripts/scale78b/build_r_draws_78b.py"
H1 = WS / "scripts/scale78b/build_h1_llama3.py"

DOC_OLD_WRAPPER = (
    '    """Refuse an output under a committed sealed folder (FORBIDDEN_DIRS) of this script\'s own checkout (REPO) or of\n'
    "    --repo, and a folder that exists and is not empty. The forbidden roots come from REPO first, so a non-default --repo\n"
    '    cannot aim --out into this checkout\'s SEAL or stage-1 folder."""\n'
)
DOC_NEW_WRAPPER = (
    '    """Refuse an output under a committed sealed folder (FORBIDDEN_DIRS) of this script\'s own checkout (REPO) or of\n'
    "    --repo, and a folder that exists and is not empty. The forbidden roots come from REPO first, so a non-default --repo\n"
    "    cannot aim --out into this checkout's SEAL or stage-1 folder. Two comparisons: the resolved paths as strings (this\n"
    "    also covers a forbidden folder that does not exist yet) and, for each forbidden folder that exists, directory\n"
    "    identity (os.path.samefile) between it and the deepest existing ancestor of out (out itself when it exists) or any\n"
    "    parent of that ancestor. Identity covers a case-variant spelling on a case-insensitive filesystem (resolve() keeps\n"
    '    the typed case), a symlink and a dotted or relative path."""\n'
)
DOC_OLD_H1 = (
    '    """Refuse an output under a committed sealed folder (FORBIDDEN_DIRS) of this script\'s own checkout (REPO) or of\n'
    "    --repo. The forbidden roots come from REPO first, so a non-default --repo cannot aim --out into this checkout's\n"
    '    SEAL, anchor or stage-1 folder. (s1.write_new_files then refuses any existing file: absent-or-empty rule.)"""\n'
)
DOC_NEW_H1 = (
    '    """Refuse an output under a committed sealed folder (FORBIDDEN_DIRS) of this script\'s own checkout (REPO) or of\n'
    "    --repo. The forbidden roots come from REPO first, so a non-default --repo cannot aim --out into this checkout's\n"
    "    SEAL, anchor or stage-1 folder. (s1.write_new_files then refuses any existing file: absent-or-empty rule.) Two\n"
    "    comparisons: the resolved paths as strings (this also covers a forbidden folder that does not exist yet) and, for\n"
    "    each forbidden folder that exists, directory identity (os.path.samefile) between it and the deepest existing\n"
    "    ancestor of out (out itself when it exists) or any parent of that ancestor. Identity covers a case-variant spelling\n"
    '    on a case-insensitive filesystem (resolve() keeps the typed case), a symlink and a dotted or relative path."""\n'
)
BODY_OLD = (
    "    out = out.resolve()\n"
    "    roots = [REPO.resolve()]\n"
    "    if repo is not None and repo.resolve() not in roots:\n"
    "        roots.append(repo.resolve())\n"
    "    for root in roots:\n"
    "        for forbidden in FORBIDDEN_DIRS:\n"
    "            target = (root / forbidden).resolve()\n"
    "            if out == target or target in out.parents:\n"
    "                raise {refusal}(f\"refusing to write under {{forbidden}}\")\n"
)
BODY_NEW = (
    "    out = out.resolve()\n"
    "    roots = [REPO.resolve()]\n"
    "    if repo is not None and repo.resolve() not in roots:\n"
    "        roots.append(repo.resolve())\n"
    "    anchor = out                                        # the deepest existing ancestor of out (out itself when it exists)\n"
    "    while not anchor.exists() and anchor.parent != anchor:\n"
    "        anchor = anchor.parent\n"
    "    for root in roots:\n"
    "        for forbidden in FORBIDDEN_DIRS:\n"
    "            target = (root / forbidden).resolve()\n"
    "            if out == target or target in out.parents:\n"
    "                raise {refusal}(f\"refusing to write under {{forbidden}}\")\n"
    "            if target.exists() and any(os.path.samefile(p, target) for p in (anchor, *anchor.parents)):\n"
    "                raise {refusal}(f\"refusing to write under {{forbidden}}\")\n"
)
EDITS = {
    SEALED: [("import json\nimport sys\n", "import json\nimport os\nimport sys\n"),
             (DOC_OLD_WRAPPER, DOC_NEW_WRAPPER),
             (BODY_OLD.format(refusal="Refusal"), BODY_NEW.format(refusal="Refusal"))],
    RDRAWS: [("import json\nimport sys\n", "import json\nimport os\nimport sys\n"),
             (DOC_OLD_WRAPPER, DOC_NEW_WRAPPER),
             (BODY_OLD.format(refusal="Refusal"), BODY_NEW.format(refusal="Refusal"))],
    H1: [("import argparse\nimport sys\n", "import argparse\nimport os\nimport sys\n"),
         (DOC_OLD_H1, DOC_NEW_H1),
         (BODY_OLD.format(refusal="s1.Refusal"), BODY_NEW.format(refusal="s1.Refusal"))],
}
for path, reps in EDITS.items():
    text = path.read_text(encoding="utf-8")
    for old, new in reps:
        assert text.count(old) == 1, f"{path.name}: anchor found {text.count(old)} times:\n{old}"
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print(f"{path.relative_to(WS)}  {hashlib.sha256(path.read_bytes()).hexdigest()}")
