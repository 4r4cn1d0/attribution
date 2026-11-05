"""Re-verifier (round 2): try to aim --out into a forbidden folder through each of the three guards, on a FAKE
checkout layout under my scratch (the real sealed folders are never an argument). Prints verdicts, paths, counts
and hashes only. Usage: python -I -B guard_probe.py <ws-c> <scratch-root>"""
import hashlib
import importlib.util
import os
import pathlib
import shutil
import sys

WS = pathlib.Path(sys.argv[1]).resolve()
ROOT = pathlib.Path(sys.argv[2]).resolve() / "probe"
if ROOT.exists():
    shutil.rmtree(ROOT)
ROOT.mkdir(parents=True)
sys.path.insert(0, str(WS))

spec = importlib.util.spec_from_file_location("bs_probe", WS / ".ai/inputs/scale-78b-sealed-llama3-20261105/build_sealed_llama3.py")
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)
from scripts.scale78b import build_r_draws_78b as B  # noqa: E402
from scripts.scale78b import build_h1_llama3 as H  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SEAL_REL, ANCH_REL, ST1_REL = W.SEAL_DIR_REL, W.ANCHORS_DIR_REL, W.STAGE1_DIR_REL
assert (W.FORBIDDEN_DIRS, B.FORBIDDEN_DIRS, H.FORBIDDEN_DIRS) == ((SEAL_REL, ANCH_REL, ST1_REL),) * 3
GUARDS = {"sealed": (W.guard_out, W.Refusal), "r-draws": (B.guard_out, B.Refusal), "h1": (H.guard_out, s1.Refusal)}
SENTINEL = b'{"sentinel": "fake sealed file, no text of the study"}\n'


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def fake_checkout(root: pathlib.Path, forbidden=True) -> pathlib.Path:
    (root / ".ai/inputs").mkdir(parents=True)
    (root / "somewhere").mkdir()
    if forbidden:
        for rel in (SEAL_REL, ANCH_REL, ST1_REL):
            (root / rel / "out").mkdir(parents=True)
        (root / SEAL_REL / "out/R_d1.json").write_bytes(SENTINEL)
        (root / ST1_REL / "length-rules/edits").mkdir(parents=True)
        (root / ST1_REL / "length-rules/edits/octile_0.json").write_bytes(SENTINEL)
    return root


fake = fake_checkout(ROOT / "fake")
fake2 = fake_checkout(ROOT / "fake2")
fake3 = fake_checkout(ROOT / "fake3", forbidden=False)             # a checkout WITHOUT the forbidden folders
seal = fake / SEAL_REL
variant = fake / ".ai/inputs/GATE-B-SEALED-20261008"
case_insensitive = variant.exists()
print(f"case-insensitive filesystem under scratch: {case_insensitive}")
link_seal = ROOT / "link-seal"; link_seal.symlink_to(seal, target_is_directory=True)
link_inputs = ROOT / "link-inputs"; link_inputs.symlink_to(fake / ".ai/inputs", target_is_directory=True)
link_repo = ROOT / "link-repo"; link_repo.symlink_to(fake, target_is_directory=True)
link_var = ROOT / "link-var"; link_var.symlink_to(variant, target_is_directory=True)   # a symlink whose TARGET is spelled in a case variant
link_chain = ROOT / "link-chain"; link_chain.symlink_to(link_repo, target_is_directory=True)   # symlink -> symlink -> fake
hl = ROOT / "hl.json"; os.link(seal / "out/R_d1.json", hl)                                  # a hard link to a file inside SEAL
hl_inode = os.stat(hl).st_ino
out_hl = ROOT / "out-hl/edits"; out_hl.mkdir(parents=True)
os.link(fake / ST1_REL / "length-rules/edits/octile_0.json", out_hl / "octile_0.json")        # a hard link planted inside a pre-made --out
out_sl = ROOT / "out-sl"; out_sl.mkdir()
(out_sl / "edits").symlink_to(fake / ST1_REL / "length-rules/edits", target_is_directory=True)  # a symlink planted inside a pre-made --out
fake_variant_repo = ROOT / "FAKE"                                                             # the fake repo itself spelled in another case
state_before = {str(p): sha(p) for p in sorted(fake.rglob("*")) if p.is_file()}
files_before = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*"))

# (label, out, repo, expected, cwd or None)
CASES = [
    ("case variant deep (SEAL/out/new)", variant / "out/new", fake, "REFUSED", None),
    ("case variant: the sealed folder itself", variant, fake, "REFUSED", None),
    ("case variant: SEAL/out", variant / "out", fake, "REFUSED", None),
    ("case variant on .ai/INPUTS (stage 1)", fake / ".ai/INPUTS/stage1-commitments-20261016/r-draws/edits", fake, "REFUSED", None),
    ("case variant anchors (Gate-B-Anchors)", fake / ".ai/inputs/Gate-B-Anchors-20261008/out/x", fake, "REFUSED", None),
    ("case variant deep, several absent components", variant / "out/a/b/c", fake, "REFUSED", None),
    ("symlink to the sealed folder", link_seal / "out/new", fake, "REFUSED", None),
    ("symlink to the sealed folder itself as --out", link_seal, fake, "REFUSED", None),
    ("symlink to a parent (.ai/inputs)", link_inputs / "gate-b-sealed-20261008/out/new", fake, "REFUSED", None),
    ("symlink to a parent + case variant after it", link_inputs / "Gate-B-Sealed-20261008/out/new", fake, "REFUSED", None),
    ("symlinked checkout root in --out", link_repo / SEAL_REL / "out/new", fake, "REFUSED", None),
    ("symlinked checkout root as --repo", seal / "out/new", link_repo, "REFUSED", None),
    ("symlinked checkout root in both", link_repo / SEAL_REL / "out/new", link_repo, "REFUSED", None),
    ("symlinked root + case variant", link_repo / ".ai/inputs/GATE-B-SEALED-20261008/out/new", fake, "REFUSED", None),
    ("symlink whose target is a case-variant spelling", link_var / "out/new", fake, "REFUSED", None),
    ("symlink chain (link -> link -> checkout)", link_chain / SEAL_REL / "out/new", fake, "REFUSED", None),
    ("symlink chain + case variant", link_chain / ".ai/inputs/gate-b-SEALED-20261008/out/new", link_chain, "REFUSED", None),
    ("dotted", fake / ".ai/inputs/elsewhere/../gate-b-sealed-20261008/./out/new", fake, "REFUSED", None),
    ("dotted + case variant", fake / "somewhere/../.ai/inputs/GATE-B-SEALED-20261008/out/new", fake, "REFUSED", None),
    ("dotted into anchors", fake / "somewhere/../.ai/inputs/gate-b-anchors-20261008/out/x", fake, "REFUSED", None),
    ("relative (cwd = fake)", pathlib.Path(".ai/inputs/gate-b-sealed-20261008/out/new"), pathlib.Path("."), "REFUSED", fake),
    ("relative + case variant (cwd = fake)", pathlib.Path(".ai/inputs/GATE-B-SEALED-20261008/out/new"), pathlib.Path("."), "REFUSED", fake),
    ("relative dotted (cwd = fake)", pathlib.Path("./somewhere/../.ai/inputs/gate-b-sealed-20261008/out/new"), pathlib.Path("."), "REFUSED", fake),
    ("relative, cwd = the symlinked root, case variant", pathlib.Path(".ai/inputs/GATE-B-SEALED-20261008/out/new"), pathlib.Path("."), "REFUSED", link_repo),
    ("relative --repo given as '..' from somewhere", pathlib.Path("../.ai/inputs/GATE-B-SEALED-20261008/out/new"), pathlib.Path(".."), "REFUSED", fake / "somewhere"),
    ("non-default --repo (fake2) into fake2's SEAL", fake2 / SEAL_REL / "out/new", fake2, "REFUSED", None),
    ("non-default --repo (fake2) into fake2's SEAL, case variant", fake2 / ".ai/inputs/GATE-B-SEALED-20261008/out/new", fake2, "REFUSED", None),
    ("non-default --repo (fake2) aimed at fake's SEAL (fake not a root)", seal / "out/new", fake2, "PASS (fake is neither REPO nor --repo)", None),
    ("--repo spelled in another case (FAKE), --out in fake's SEAL", seal / "out/new", fake_variant_repo, "REFUSED", None),
    ("--repo spelled in another case (FAKE), --out case variant too", fake_variant_repo / ".ai/inputs/gate-b-sealed-20261008/out/new", fake_variant_repo, "REFUSED", None),
    ("--repo without the forbidden folders (fake3), exact string", fake3 / SEAL_REL / "out/new", fake3, "REFUSED", None),
    ("--repo without the forbidden folders (fake3), case variant [string only: a stated limit]", fake3 / ".ai/inputs/GATE-B-SEALED-20261008/out/new", fake3, "PASS (no inode to compare)", None),
    ("parent is a file inside SEAL", seal / "out/R_d1.json/new", fake, "REFUSED", None),
    ("hard link to a file inside SEAL as --out", hl, fake, "NOT A REFUSAL (see write test)", None),
    ("pre-made --out holding a hard link to a stage-1 file", ROOT / "out-hl", fake, "REFUSED by non-empty (sealed, r-draws); PASS for h1 (write_new_files refuses later)", None),
    ("pre-made --out holding a symlink to a stage-1 folder", out_sl, fake, "REFUSED by non-empty (sealed, r-draws); PASS for h1 (write_new_files refuses later)", None),
    ("control: sibling with a shared prefix", fake / ".ai/inputs/gate-b-sealed-20261008-copy/out", fake, "PASS", None),
    ("control: an ordinary new folder", fake / ".ai/inputs/new-folder/out", fake, "PASS", None),
    ("control: relative ordinary (cwd = fake)", pathlib.Path("somewhere/out"), pathlib.Path("."), "PASS", fake),
    ("control: fake3 ordinary", fake3 / "somewhere/out", fake3, "PASS", None),
]

results = {}
cwd0 = os.getcwd()
for label, out, repo, expected, cwd in CASES:
    row = {}
    for gname, (guard, refusal) in GUARDS.items():
        if cwd is not None:
            os.chdir(cwd)
        try:
            guard(out, repo)
            row[gname] = "PASS"
        except refusal as exc:
            msg = str(exc)
            row[gname] = "REFUSED: " + ("refusing to write under " + msg.split("refusing to write under ")[-1] if "refusing to write under" in msg
                                        else "non-empty" if "not empty" in msg else msg[:60])
        except Exception as exc:  # noqa: BLE001
            row[gname] = f"ERROR {type(exc).__name__}"
        finally:
            os.chdir(cwd0)
    results[label] = row
    verdicts = {v.split(":")[0].split(" ")[0] for v in row.values()}
    print(f"[{label}] expected {expected}")
    for gname, v in row.items():
        print(f"    {gname:8s} {v}")

# ---- the CLIs on the fake checkout (they can only refuse or fail before any write: the fake holds no inputs)
print("\nCLI (main) on the fake checkout:")
import io, contextlib  # noqa: E402
def cli(label, fn, argv):
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = fn(argv)
        print(f"    {label}: exit {code}; stderr: {err.getvalue().strip()[:120]}")
    except Exception as exc:  # noqa: BLE001
        print(f"    {label}: ERROR {type(exc).__name__} (not a Refusal; nothing written)")
cli("sealed --repo fake --out case variant", W.main, ["--repo", str(fake), "--out", str(variant / "out/new")])
cli("sealed --repo link-repo --out case variant via link", W.main, ["--repo", str(link_repo), "--out", str(link_repo / ".ai/inputs/GATE-B-SEALED-20261008/out/new")])
cli("sealed --out ok --olmo-parity-out case variant", W.main, ["--repo", str(fake), "--out", str(ROOT / "ok1"), "--olmo-parity-out", str(variant / "out/p")])
cli("sealed --out hard link to a SEAL file", W.main, ["--repo", str(fake), "--out", str(hl)])
cli("r-draws --repo fake --out case variant", B.main, ["--repo", str(fake), "--out", str(variant / "out/new")])
cli("r-draws --repo FAKE (case) --out exact", B.main, ["--repo", str(fake_variant_repo), "--out", str(seal / "out/new")])
cli("r-draws --out hard link to a SEAL file", B.main, ["--repo", str(fake), "--out", str(hl)])
cli("h1 --repo fake --out case variant", H.main, ["--repo", str(fake), "--out", str(variant / "out/new")])
cli("h1 --repo link-chain --out via chain + case", H.main, ["--repo", str(link_chain), "--out", str(link_chain / ".ai/inputs/gate-b-SEALED-20261008/out/new")])
cli("h1 --out hard link to a SEAL file", H.main, ["--repo", str(fake), "--out", str(hl)])
cli("h1 --out pre-made folder with a planted hard link", H.main, ["--repo", str(fake), "--out", str(ROOT / "out-hl")])

# ---- the write functions behind the guards, on the hard-link and planted cases (my scratch only)
print("\nWrite functions on the hard-link / planted cases:")
def attempt(label, fn, *a):
    try:
        fn(*a)
        print(f"    {label}: WROTE (no refusal)")
    except (W.Refusal, B.Refusal, s1.Refusal) as exc:
        print(f"    {label}: REFUSED ({str(exc).split(':')[-1].strip()[:50]})")
    except Exception as exc:  # noqa: BLE001
        print(f"    {label}: ERROR {type(exc).__name__}")
attempt("W.write_files(hard link to a SEAL file, ...)", W.write_files, hl, {"x.json": b"1"})
attempt("B.write_files(hard link to a SEAL file, ...)", B.write_files, hl, {"x.json": b"1"})
attempt("s1.write_new_files(hard link to a SEAL file, ...)", s1.write_new_files, hl, {"x.json": b"1"})
attempt("s1.write_new_files(out-hl with a planted hard link, octile_0)", s1.write_new_files, ROOT / "out-hl", {"edits/octile_0.json": b"NEW"})
attempt("s1.write_new_files(out-sl with a planted symlink, octile_0)", s1.write_new_files, out_sl, {"edits/octile_0.json": b"NEW"})

# ---- nothing inside the fake forbidden folders changed; the hard-linked inode is untouched
state_after = {str(p): sha(p) for p in sorted(fake.rglob("*")) if p.is_file()}
files_after = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*"))
print("\nfake checkout files unchanged:", state_before == state_after, f"({len(state_after)} files)")
print("hard link inode unchanged:", os.stat(hl).st_ino == hl_inode, "content unchanged:", hl.read_bytes() == SENTINEL)
print("new entries under the probe root:", sorted(set(files_after) - set(files_before)))
print("SEAL/out entries:", sorted(p.name for p in (seal / "out").iterdir()))
print("stage-1 octile sentinel unchanged:", (fake / ST1_REL / "length-rules/edits/octile_0.json").read_bytes() == SENTINEL)
shutil.rmtree(ROOT)
print("probe root removed")
