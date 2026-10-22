"""REQ-20 (brief rev 1; AUDIT closure 9) with W1-17 and LN-30: the stage-1 W1 commitments manifest and its checker.
Mac, $0; the lead runs it in the main checkout. It prints counts and hashes only.

    python scripts/stage1/commitments.py build --repo ROOT      # after the W1 files are committed; writes the manifest
    python scripts/stage1/commitments.py check --repo ROOT [--manifest PATH]

**Generated from the committed tree (the lead's 17 Oct ruling).** ``build`` reads the tree of HEAD through git, never
the working copy, and lists every tracked file that an include rule of the settings matches (scripts/stage1/**,
scripts/stage1_s1/**, the sealed records' folder) plus the rule-text paths the settings name. So the S1 package's files
and Part E revision 2's files only need to be committed; no hash is typed in by hand. ``build`` first refuses an
uncommitted change or an untracked file under an include rule, then writes the manifest (never over an existing file).
The lead commits it.

**LN-30, the commit order.** The manifest is committed first; the REQ-21 record carries the manifest's SHA-256, so the
manifest cannot list it; then FOCUS; then wave 1. The settings' exclusions name the REQ-21 record (and the manifest
itself), the manifest lists every excluded path it saw with its reason, and the checker accepts a manifest without the
record and refuses one that lists an excluded path.

**Entries.** Per file: path (its id), role (by the first matching role rule; a sealed record whose kind is a prediction
kind gets the role "prediction"), SHA-256, bytes, deadline W1, the requirement, W1 item, SCOPE tier and D5 mark of the
first matching requirement rule (null if none), the conditional flag with the condition text (W1-17; the settings'
conditional rules), and made_by (the provenance block's script, script SHA-256 and settings SHA-256 for a record that
has one, else "authored (tracked file)"). Also: the base commit, engine X, PREREG's path and SHA-256 (checked against
the pin), the not-built entries {id, item, reason, label} (W1-17; every not-built row of the REQ-21
record's (l) table, its label copied from (l) out of the fixed set the settings list; addendum section 14), the labels appended after
T1 with their named_in (each must start "registry, after the seal"), and the full files under tmp/ named by SHA-256
only (copied from the records' full_file and full_files blocks).

**Text-bearing files refuse** (a schema allow-list): a JSON file anywhere whose kind is a text-bearing kind; a sealed
record whose kind is not on the text-free allow-list; an edit file with add or rewrite rows.

**The checker** validates the manifest's own fields (W1-17: a conditional entry carries the condition text, a not-built
entry carries the label, no excluded path is listed), regenerates the manifest from its base commit with the same
settings and compares, checks that the base commit is an ancestor of HEAD, and then, per entry, refuses a missing file,
a changed byte, a path that git does not track at HEAD, and a file that differs from HEAD. A file committed after the
base commit under the include rules is not listed, but it is classified as the build classifies, so a text-bearing
kind committed later refuses too (C3).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "commitments.json"
SETTINGS_SHA256 = "0e4dcb589f7d8f4eb66f02de83f352ea4752b94000b7e2b76b9dff5232cac837"
SETTINGS_NAME = "commitments"
COMMIT = re.compile(r"^[0-9a-f]{40}$")
COMPARED = ("kind", "version", "base_commit", "engine_x", "prereg", "settings_sha256", "rules", "entries", "excluded",
            "not_built", "appended_labels", "full_files", "counts", "lists_req21_record")


# ----- git (read-only) ---------------------------------------------------------------------------------------------


def git(root: Path, *args: str, data: bytes | None = None, ok=(0,)) -> bytes:
    env = {**os.environ, "LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0"}
    try:
        proc = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=off", *args], input=data,
                              capture_output=True, env=env, check=False)
    except OSError as exc:
        raise s1.Refusal(f"git cannot run ({type(exc).__name__})") from None
    if proc.returncode not in ok:
        raise s1.Refusal(f"git {args[0]} failed (exit {proc.returncode})")
    return proc.stdout


def is_ancestor(root: Path, older: str, newer: str) -> bool:
    proc = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", older, newer], capture_output=True,
                          env={**os.environ, "LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0"}, check=False)
    if proc.returncode not in (0, 1):
        raise s1.Refusal(f"git merge-base failed (exit {proc.returncode})")
    return proc.returncode == 0


def check_root(root: Path) -> Path:
    root = Path(root).resolve()
    top = git(root, "rev-parse", "--show-toplevel").decode().strip()
    if Path(top).resolve() != root:
        raise s1.Refusal("--repo is not the top folder of a git repository")
    return root


def resolve(root: Path, rev: str) -> str:
    sha = git(root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}", ok=(0, 1)).decode().strip()
    if not COMMIT.match(sha):
        raise s1.Refusal(f"{rev} is not a commit of this repository")
    return sha


def tree_files(root: Path, commit: str) -> list[str]:
    out = git(root, "ls-tree", "-r", "-z", "--name-only", commit)
    return sorted(p.decode() for p in out.split(b"\0") if p)


def blobs(root: Path, commit: str, paths: list[str]) -> dict[str, bytes]:
    """The bytes of each path at commit (git cat-file --batch)."""
    if not paths:
        return {}
    out = git(root, "cat-file", "--batch", data="".join(f"{commit}:{p}\n" for p in paths).encode())
    result, pos = {}, 0
    for path in paths:
        end = out.index(b"\n", pos)
        header = out[pos:end].split()
        if len(header) != 3 or header[1] != b"blob":
            raise s1.Refusal(f"{path} is not a file at {commit}")
        size = int(header[2])
        result[path] = out[end + 1:end + 1 + size]
        pos = end + 1 + size + 1
    return result


# ----- the rules ---------------------------------------------------------------------------------------------------


def glob_regex(pattern: str) -> re.Pattern:
    """A path glob: ** crosses folders (and "**/" may match nothing), * and ? stay inside one folder name."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile("^" + out + "$")


def first_match(path: str, rules: list[dict]):
    return next((rule for rule in rules if glob_regex(rule["glob"]).match(path)), None)


def matches(path: str, globs: list[str]) -> bool:
    return any(glob_regex(g).match(path) for g in globs)


def selected(paths: list[str], settings: dict) -> tuple[list[str], list[dict]]:
    """(the included paths, the excluded paths with their reasons) among paths."""
    included, excluded = [], []
    for path in paths:
        if not (matches(path, settings["include"]) or path in settings["rule_text"]):
            continue
        rule = first_match(path, settings["exclude"])
        if rule is not None:
            excluded.append({"path": path, "reason": rule["reason"]})
        else:
            included.append(path)
    return included, excluded


def classify(path: str, data: bytes, settings: dict) -> tuple[str, dict | None]:
    """(role, the parsed JSON document or None); refuses a text-bearing file and a file without a role."""
    if path in settings["rule_text"]:
        role = "rule text"
    else:
        rule = first_match(path, settings["roles"])
        if rule is None:
            raise s1.Refusal(f"{path}: no role rule matches it")
        role = rule["role"]
    doc = None
    if path.endswith(".json"):
        try:
            doc = s1.strict_json(data)
        except s1.Refusal:
            raise s1.Refusal(f"{path}: not a JSON document") from None
    kind = doc.get("kind") if isinstance(doc, dict) else None
    if kind in settings["text_bearing_kinds"]:
        raise s1.Refusal(f"{path}: a text-bearing kind ({kind}) is committed")
    if role == "sealed record":
        if kind == settings["edit_kind"]:
            if doc.get("add") or doc.get("rewrite"):
                raise s1.Refusal(f"{path}: an edit file with add or rewrite rows holds text")
        elif kind in settings["prediction_kinds"]:
            role = "prediction"
        elif kind not in settings["text_free_kinds"]:
            raise s1.Refusal(f"{path}: a sealed record whose kind ({kind}) is not on the text-free allow-list")
    return role, doc


def made_by(doc) -> dict | str:
    prov = doc.get("provenance") if isinstance(doc, dict) else None
    if isinstance(prov, dict) and isinstance(prov.get("script"), str) and isinstance(prov.get("script_sha256"), str):
        return {"script": prov["script"], "script_sha256": prov["script_sha256"],
                "settings_sha256": prov.get("settings_sha256")}
    return "authored (tracked file)"


def full_files_of(path: str, doc) -> list[dict]:
    out = []
    if isinstance(doc, dict):
        full = doc.get("full_file")
        if isinstance(full, dict) and isinstance(full.get("sha256"), str):
            out.append({"record": path, "name": None, "sha256": full["sha256"], "bytes": full.get("bytes")})
        named = doc.get("full_files")
        if isinstance(named, dict):
            out += [{"record": path, "name": n, "sha256": sha, "bytes": None} for n, sha in sorted(named.items())
                    if isinstance(sha, str)]
    return out


def appended_labels(labels: bytes, t1: bytes, settings: dict) -> list[dict]:
    reg, pinned = s1.strict_json(labels), s1.strict_json(t1)
    entries = {**reg["labels"], **reg["frozen_reused"]}
    out = []
    for key in sorted(set(entries) - set(pinned["entries"])):
        entry = entries[key]
        if not str(entry.get("named_in", "")).startswith(settings["appended_named_in"]):
            raise s1.Refusal(f"label {key} was appended after T1 but is not named in 'registry, after the seal'")
        out.append({"key": key, "label": entry["label"], "owner": entry["owner"], "named_in": entry["named_in"]})
    return out


def generate(root: Path, commit: str, settings: dict, settings_sha256: str) -> dict:
    """The manifest of commit's tree (no working-copy byte is read)."""
    files = tree_files(root, commit)
    missing = sorted(set(settings["rule_text"]) - set(files))
    if missing:
        raise s1.Refusal(f"{len(missing)} rule-text paths are not tracked at {commit} (first: {missing[0]})")
    prereg = settings["prereg"]
    registry = settings["registry"]
    if prereg["path"] not in files or registry["labels"] not in files or registry["t1_entries"] not in files:
        raise s1.Refusal(f"PREREG or the label registry is not tracked at {commit}")
    included, excluded = selected(files, settings)
    data = blobs(root, commit, included + [prereg["path"], registry["labels"], registry["t1_entries"]])
    if sha256_bytes(data[prereg["path"]]) != prereg["sha256"]:
        raise s1.Refusal(f"PREREG hashes to {sha256_bytes(data[prereg['path']])} at {commit}, the pin is {prereg['sha256']}")
    entries, full = [], []
    for path in included:
        role, doc = classify(path, data[path], settings)
        req = first_match(path, settings["requirements"]) or {}
        cond = first_match(path, settings["conditional"]["rules"])
        entries.append({"path": path, "role": role, "sha256": sha256_bytes(data[path]), "bytes": len(data[path]),
                        "deadline": settings["deadline"], "requirement": req.get("req"), "item": req.get("item"),
                        "tier": req.get("tier"), "d5": req.get("d5"), "conditional": cond is not None,
                        "condition": settings["conditional"]["text"] if cond is not None else None,
                        "made_by": made_by(doc)})
        full += full_files_of(path, doc)
    by_role: dict[str, int] = {}
    for e in entries:
        by_role[e["role"]] = by_role.get(e["role"], 0) + 1
    return {"kind": settings["manifest"]["kind"], "version": settings["manifest"]["version"], "base_commit": commit,
            "engine_x": settings["engine_x"], "prereg": {"path": prereg["path"], "sha256": prereg["sha256"]},
            "settings_sha256": settings_sha256,
            "rules": {k: settings[k] for k in ("include", "rule_text", "exclude")},
            "entries": entries, "excluded": excluded, "not_built": settings["not_built"],
            "appended_labels": appended_labels(data[registry["labels"]], data[registry["t1_entries"]], settings),
            "full_files": full, "counts": {"entries": len(entries), "by_role": dict(sorted(by_role.items())),
                                           "excluded": len(excluded), "not_built": len(settings["not_built"]),
                                           "full_files": len(full)},
            "lists_req21_record": False, "commit_order": settings["commit_order"],
            "generator": {"script": s1.rel(Path(__file__).resolve()), "script_sha256": sha256_file(Path(__file__).resolve())}}


def validate(manifest: dict, settings: dict) -> None:
    """W1-17's own checks on a manifest's fields, and LN-30's."""
    if not isinstance(manifest, dict) or manifest.get("kind") != settings["manifest"]["kind"] or \
            manifest.get("version") != settings["manifest"]["version"]:
        raise s1.Refusal("not a stage-1 W1 commitments manifest")
    if not isinstance(manifest.get("base_commit"), str) or not COMMIT.match(manifest["base_commit"]):
        raise s1.Refusal("the manifest names no base commit")
    paths = [e.get("path") for e in manifest.get("entries", [])]
    if paths != sorted(set(paths)):
        raise s1.Refusal("the manifest's entries are not distinct paths in sorted order")
    for e in manifest["entries"]:
        if e.get("conditional") is True and e.get("condition") != settings["conditional"]["text"]:
            raise s1.Refusal(f"{e['path']}: a conditional entry without its condition text")
        if e.get("conditional") is not True and e.get("condition") is not None:
            raise s1.Refusal(f"{e['path']}: a condition text on an entry that is not conditional")
        if first_match(e["path"], settings["exclude"]) is not None:
            raise s1.Refusal(f"{e['path']}: the manifest lists an excluded path (LN-30)")
    for nb in manifest.get("not_built", []):
        if nb.get("label") not in settings["not_built_labels"] or not nb.get("reason") or not nb.get("id"):
            raise s1.Refusal(f"a not-built entry ({nb.get('id')}) without its id, reason or a label from the fixed set")
    if manifest.get("lists_req21_record") is not False:
        raise s1.Refusal("the manifest says it lists the REQ-21 record (LN-30)")


def worktree_dirty(root: Path, settings: dict) -> list[str]:
    changed = [p.decode() for p in git(root, "diff", "--name-only", "-z", "HEAD").split(b"\0") if p]
    untracked = [p.decode() for p in git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p]
    return sorted(p for p in set(changed) | set(untracked)
                  if (matches(p, settings["include"]) or p in settings["rule_text"])
                  and first_match(p, settings["exclude"]) is None)


def build(root: Path, settings: dict, settings_sha256: str) -> tuple[Path, bytes]:
    s1.check_settings(settings, SETTINGS_NAME)
    root = check_root(root)
    dirty = worktree_dirty(root, settings)
    if dirty:
        raise s1.Refusal(f"{len(dirty)} files under the include rules are uncommitted or untracked (first: {dirty[0]})")
    manifest = generate(root, resolve(root, "HEAD"), settings, settings_sha256)
    validate(manifest, settings)
    out = root / settings["manifest"]["path"]
    if out.exists():
        raise s1.Refusal(f"{settings['manifest']['path']} exists: a manifest is never overwritten")
    return out, canonical_json(manifest)


def check(root: Path, manifest_path: Path | None, settings: dict, settings_sha256: str) -> dict:
    s1.check_settings(settings, SETTINGS_NAME)
    root = check_root(root)
    path = manifest_path or root / settings["manifest"]["path"]
    try:
        manifest = s1.strict_json(Path(path).read_bytes())
    except OSError as exc:
        raise s1.Refusal(f"the manifest cannot be read ({type(exc).__name__})") from None
    validate(manifest, settings)
    if manifest.get("settings_sha256") != settings_sha256:
        raise s1.Refusal("the manifest was made with other settings")
    base = resolve(root, manifest["base_commit"])
    head = resolve(root, "HEAD")
    if not is_ancestor(root, base, head):
        raise s1.Refusal("the manifest's base commit is not an ancestor of HEAD")
    expected = generate(root, base, settings, settings_sha256)
    for key in COMPARED:
        if manifest.get(key) != expected[key]:
            raise s1.Refusal(f"the manifest's {key} differs from the base commit's regenerated manifest")
    at_head = set(tree_files(root, head))
    listed = [e["path"] for e in manifest["entries"]]
    head_bytes = blobs(root, head, [p for p in listed if p in at_head])
    for e in manifest["entries"]:
        file = root / e["path"]
        if not file.is_file():
            raise s1.Refusal(f"{e['path']}: the file is missing")
        if sha256_file(file) != e["sha256"]:
            raise s1.Refusal(f"{e['path']}: a changed byte (it hashes to {sha256_file(file)})")
        if e["path"] not in at_head:
            raise s1.Refusal(f"{e['path']}: git does not track it at HEAD")
        if sha256_bytes(head_bytes[e["path"]]) != e["sha256"]:
            raise s1.Refusal(f"{e['path']}: the file at HEAD differs from the manifest")
    # C3: a file committed after the base commit under the include rules is not listed, but it is classified as the
    # build classifies (a text-bearing kind, an edit file with text, an unknown sealed kind or a path without a role refuses)
    included_head, _ = selected(list(at_head), settings)
    later = [p for p in included_head if p not in set(listed)]
    head_later = blobs(root, head, later)
    for p in later:
        classify(p, head_later[p], settings)
    return {"entries": len(listed), "by_role": manifest["counts"]["by_role"], "base_commit": base, "head": head,
            "excluded": len(manifest["excluded"]), "not_built": len(manifest["not_built"]), "later_files": len(later)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        if args.command == "build":
            out, data = build(args.repo, settings, digest)
            out.parent.mkdir(parents=True, exist_ok=True)
            s1.write_atomic(out, data)
            if sha256_file(out) != sha256_bytes(data):
                raise s1.Refusal("the manifest did not read back as written")
            doc = json.loads(data)
            print(f"  {sha256_bytes(data)}  {s1.rel(out)}  ({doc['counts']['entries']} entries, base "
                  f"{doc['base_commit']})")
        else:
            result = check(args.repo, args.manifest, settings, digest)
            print(f"  OK: {result['entries']} entries {json.dumps(result['by_role'], sort_keys=True)}; base "
                  f"{result['base_commit']}; HEAD {result['head']}; {result['excluded']} excluded; "
                  f"{result['not_built']} not built; {result['later_files']} files committed later, classified")
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
