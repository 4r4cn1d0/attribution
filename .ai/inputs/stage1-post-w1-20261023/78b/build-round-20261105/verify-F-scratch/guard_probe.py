"""Verifier's write-guard probes for build_s1_llama3.py on FAKE layouts under the scratch folder only.
Usage: <venv> -I -B guard_probe.py <repo copy> <scratch>"""
import importlib.util
import os
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
SCR = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(REPO))
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import build_s_pool as bsp  # noqa: E402
from scripts.stage1 import write_add_edit as wae  # noqa: E402

spec = importlib.util.spec_from_file_location("w", REPO / ".ai/inputs/scale-78b-s1-llama3-20261105/build_s1_llama3.py")
W = importlib.util.module_from_spec(spec)
spec.loader.exec_module(W)

SEALED = W.FORBIDDEN_DIRS[3]        # .ai/inputs/scale-78b-sealed-llama3-20261105
results = []


def probe(label, fn, expect):
    try:
        fn()
        got = "ALLOWED"
    except s1.Refusal as exc:
        got = "REFUSED"
    except Exception as exc:  # noqa: BLE001
        got = f"ERROR {type(exc).__name__}"
    ok = "ok" if got.startswith(expect) else "**UNEXPECTED**"
    results.append((label, got, expect, ok))
    print(f"{ok:14s} {got:10s} (expected {expect:8s}) {label}")


def fake_checkout(root):
    for rel in W.FORBIDDEN_DIRS:
        (root / rel / "out").mkdir(parents=True)
        (root / rel / "out" / "MANIFEST.json").write_text("{}")
    (root / "tmp").mkdir()
    return root


A = fake_checkout(SCR / "fakeA")
B = fake_checkout(SCR / "fakeB")
probeA = SCR / "Probe-Case"
probeA.mkdir()
case_insensitive = (SCR / "probe-case").exists()
print("filesystem case-insensitive:", case_insensitive)
W.REPO = A                                # the script "lives" in checkout A

# 1 plain refusals
probe("A sealed out/ itself (repo=A)", lambda: W.guard_out(A / SEALED / "out", A), "REFUSED")
probe("A sealed deeper (repo=None)", lambda: W.guard_out(A / SEALED / "out" / "deeper" / "x", None), "REFUSED")
probe("A sealed folder root itself", lambda: W.guard_out(A / SEALED, A), "REFUSED")
probe("A elsewhere under tmp", lambda: W.guard_out(A / "tmp" / "free", A), "ALLOWED")
# 2 case variants
if case_insensitive:
    upper = A / ".ai" / "inputs" / SEALED.split("/")[-1].upper() / "out" / "new"
    probe("case variant of an EXISTING sealed folder", lambda: W.guard_out(upper, A), "REFUSED")
    upper2 = A / ".AI" / "INPUTS" / SEALED.split("/")[-1] / "out" / "new"
    probe("case variant on .AI/INPUTS", lambda: W.guard_out(upper2, A), "REFUSED")
    mixed = A / ".ai" / "inputs" / "Scale-78b-Sealed-Llama3-20261105" / "OUT" / "new"
    probe("mixed case on the folder and OUT", lambda: W.guard_out(mixed, A), "REFUSED")
    # a forbidden folder that does not exist in this checkout: a case variant is not refused (nothing sealed there)
    C = SCR / "fakeC"
    (C / ".ai" / "inputs").mkdir(parents=True)
    W.REPO = C
    probe("case variant where the sealed folder does NOT exist (checkout C)",
          lambda: W.guard_out(C / ".ai" / "inputs" / SEALED.split("/")[-1].upper() / "out", C), "ALLOWED")
    W.REPO = A
# 3 symlinks
link = SCR / "link-to-sealed"
link.symlink_to(A / SEALED)
probe("symlink to the sealed folder, out below it", lambda: W.guard_out(link / "out" / "new", A), "REFUSED")
link_out = SCR / "link-to-sealed-out"
link_out.symlink_to(A / SEALED / "out")
probe("symlink to the sealed out/, new file below", lambda: W.guard_out(link_out / "new", A), "REFUSED")
link_parent = SCR / "link-to-inputs"
link_parent.symlink_to(A / ".ai" / "inputs")
probe("symlink to .ai/inputs then the sealed name", lambda: W.guard_out(link_parent / SEALED.split("/")[-1] / "out" / "n", A), "REFUSED")
if case_insensitive:
    probe("symlink + case variant", lambda: W.guard_out(link_parent / SEALED.split("/")[-1].upper() / "out" / "n", A), "REFUSED")
# 4 dotted and relative
probe("dotted path .ai/inputs/./sealed/out/new", lambda: W.guard_out(A / ".ai" / "inputs" / "." / SEALED.split("/")[-1] / "out" / "new", A), "REFUSED")
probe("dot-dot traversal tmp/../.ai/inputs/sealed/out", lambda: W.guard_out(A / "tmp" / ".." / SEALED / "out" / "new", A), "REFUSED")
os.chdir(A)
probe("relative path from the checkout root", lambda: W.guard_out(Path(SEALED) / "out" / "x", A), "REFUSED")
probe("relative path with ./", lambda: W.guard_out(Path(".") / SEALED / "out" / "x", A), "REFUSED")
os.chdir(A / "tmp")
probe("relative path from tmp/ with ..", lambda: W.guard_out(Path("..") / SEALED / "out" / "x", A), "REFUSED")
os.chdir(SCR)
# 5 cross-checkout: the script lives in A; the output is B's sealed folder
probe("B's sealed folder, repo=None (script in A)", lambda: W.guard_out(B / SEALED / "out" / "new", None), "REFUSED")
probe("B's sealed folder, repo=A (script in A)", lambda: W.guard_out(B / SEALED / "out" / "new", A), "REFUSED")
probe("B's sealed folder, repo=B", lambda: W.guard_out(B / SEALED / "out" / "new", B), "REFUSED")
# 6 the S1 folder's own out/ is not a FORBIDDEN_DIR: only the non-empty rule protects it
own = A / ".ai/inputs/scale-78b-s1-llama3-20261105"
(own / "out").mkdir(parents=True)
(own / "out" / "MANIFEST.json").write_text("{}")
probe("the S1 folder's own committed out/ (guard_out alone)", lambda: W.guard_out(own / "out", A), "ALLOWED")
probe("the S1 folder's own committed out/ (check_output_folders)", lambda: bsp.check_output_folders(own / "out"), "REFUSED")
probe("a new out2/ beside the committed out/ in the S1 folder", lambda: (W.guard_out(own / "out2", A), bsp.check_output_folders(own / "out2")), "ALLOWED")
probe("--full-out inside the S1 sealed folder under a 'tmp' name (text into the sealed tree)",
      lambda: (W.guard_out(own / "tmp" / "x", A), wae.full_out_ok(own / "tmp" / "x")), "ALLOWED")
# 7 a hard link to a sealed FILE as --out
hard = SCR / "hardlink-manifest.json"
os.link(A / SEALED / "out" / "MANIFEST.json", hard)
probe("hard link to a sealed file as --out (guard_out)", lambda: W.guard_out(hard, A), "ALLOWED")
probe("hard link to a sealed file as --out (check_output_folders)", lambda: bsp.check_output_folders(hard), "REFUSED")
# 8 --full-out not under tmp
probe("--full-out with no 'tmp' component", lambda: wae.full_out_ok(Path("/Users/nobody/x/y")), "REFUSED")
probe("--full-out with 'tmp' only as a file-name prefix (tmpdir)", lambda: wae.full_out_ok(Path("/Users/nobody/tmpdir/y")), "REFUSED")
print()
print("unexpected:", [r[0] for r in results if r[3] != "ok"] or "none")
