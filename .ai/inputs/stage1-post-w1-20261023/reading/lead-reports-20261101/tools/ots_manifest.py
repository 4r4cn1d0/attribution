"""The manifest that the OpenTimestamps stamp binds (the user, 31 Oct: "Yes, time-stamp it", in place of the OSF
posting). It lists, by SHA-256 only: the anonymized deposit package (the zip and each member), the frozen originals
named in the package's HASHES.json (each checked at its commit and in the working tree), the two block seal records,
and git's own ids for HEAD and the stage-1 code trees. No file text, no outcome. Exclusive create.

    PY -B ots_manifest.py ROOT PACKAGE_DIR OUT
"""
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys
import zipfile

root, pkg, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(*args) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True).stdout


zip_path = pkg / "osf-deposit-20261023-anon.zip"
zf = zipfile.ZipFile(zip_path)
members = {}
for name in zf.namelist():
    data = zf.read(name)
    loose = (pkg / name).read_bytes()
    if sha(data) != sha(loose):
        sys.exit(f"refused: zip member {name} differs from the loose file")
    members[name] = sha(data)

hashes = json.loads((pkg / "HASHES.json").read_bytes())
originals = []
for entry in hashes["files"]:
    at_commit = sha(git("show", f"{entry['original_commit']}:{entry['original_path']}"))
    work = root / entry["original_path"]
    in_tree = sha(work.read_bytes()) if work.is_file() else None
    if at_commit != entry["original_sha256"]:
        sys.exit(f"refused: {entry['original_path']} at {entry['original_commit'][:8]} is {at_commit[:8]}, "
                 f"HASHES.json says {entry['original_sha256'][:8]}")
    originals.append({"path": entry["original_path"], "sha256": entry["original_sha256"],
                      "commit": entry["original_commit"], "commit_utc": entry.get("original_commit_utc"),
                      "checked_at_commit": True, "working_tree_equal": in_tree == entry["original_sha256"],
                      "package_file": entry["file"], "package_sha256": members.get(entry["file"])})

seals = {}
for block in ("A", "B"):
    p = root / "tmp" / "stage1-olmo" / "seals" / f"block-{block}.json"
    seals[f"block-{block}"] = {"path": f"tmp/stage1-olmo/seals/block-{block}.json", "file_sha256": sha(p.read_bytes())}

head = git("rev-parse", "HEAD").decode().strip()
trees = {path: git("rev-parse", f"HEAD:{path}").decode().strip()
         for path in ("scripts/stage1", "scripts/stage1_s1", "runkit/stage1-olmo", "scripts/gate_b_mac_judges")}

doc = {
    "kind": "stage1 outside time stamp manifest (OpenTimestamps)",
    "version": 1,
    "purpose": "An outside time stamp, before the stage-1 reading, of the frozen stage-1 rules (the anonymized OSF "
               "deposit package and the committed originals it names), the two block seal records and the code "
               "state. The user chose this in place of the OSF posting; under the frozen wording rule "
               "(stage-1 pre-registration revision 4, the 'pre-registered' row) the paper says 'pre-specified'.",
    "decision": {"question": "Shall I time-stamp the rules with OpenTimestamps instead of OSF?",
                 "user_words": "Yes, time-stamp it", "recorded_by": "General Implementation VIII (the lead)"},
    "package": {"folder": "tmp/osf-deposit-20261023 (built 2026-10-23; a copy of the zip is committed beside this "
                          "manifest)",
                "zip": {"file": zip_path.name, "sha256": sha(zip_path.read_bytes())},
                "members": dict(sorted(members.items())),
                "hashes_json_sha256": sha((pkg / "HASHES.json").read_bytes())},
    "originals": originals,
    "seals": seals,
    "git": {"head": head, "trees": trees, "note": "git object ids (SHA-1) of the committed trees at HEAD"},
    "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
}
text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
with out.open("x") as handle:
    handle.write(text)
print(json.dumps({"written": str(out), "sha256": sha(out.read_bytes()), "members": len(members),
                  "originals": len(originals), "all_in_tree": all(o["working_tree_equal"] for o in originals),
                  "head": head[:12]}))
