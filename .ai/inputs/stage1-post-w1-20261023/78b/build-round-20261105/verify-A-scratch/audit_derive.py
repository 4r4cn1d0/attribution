"""Verifier's own audit hook over the builder's derive_78b_basis.py on the real root: every open() under the root is
recorded by MY hook (installed before the import); the distinct basenames and the count are printed; the re-derived
basis goes to a scratch path and its SHA-256 is compared with the pinned one and with the worktree file's bytes."""
import hashlib, pathlib, sys

KIT = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-a/runkit/stage1-78b")
ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp")
OUT = pathlib.Path(sys.argv[1])
ALLOWED = {"verification.json", "finished.json", "create-intent.json", "create-result.json", "BOOTSTRAP-READY.json",
           "PREFLIGHT-DONE.json", "JOB-DONE.json", "ledger.jsonl", "progress.jsonl"}
opened = []


def hook(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, pathlib.Path)):
        p = str(args[0])
        if p.startswith(str(ROOT)):
            opened.append(p)


sys.addaudithook(hook)
sys.path.insert(0, str(KIT))
import derive_78b_basis as D  # noqa: E402

basis = D.derive(ROOT)
data = D.canonical(basis)
OUT.write_bytes(data)
digest = hashlib.sha256(data).hexdigest()
pinned = "fc92a568b0556f7718a1c27e488e62072df758942deef0ad7dee6d9d80cddc40"
names = sorted({pathlib.Path(p).name for p in opened})
bad = [p for p in opened if pathlib.Path(p).name not in ALLOWED]
forb = [p for p in opened if any(part in D.FORBIDDEN_PARTS for part in pathlib.Path(p).parts)]
kits = sorted({pathlib.Path(p).relative_to(ROOT).parts[0] for p in opened})
print("opens under root:", len(opened), "distinct basenames:", names)
print("kits touched:", len(kits), "names outside allow-list:", len(bad), "forbidden parts:", len(forb))
print("units:", len(basis["units"]), "sha256:", digest, "== pinned:", digest == pinned,
      "== worktree bytes:", data == (KIT / "measured-basis-78b.json").read_bytes())
sys.exit(0 if (not bad and not forb and digest == pinned) else 1)
