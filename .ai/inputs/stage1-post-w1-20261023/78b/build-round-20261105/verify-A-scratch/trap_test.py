"""Verifier's own privacy trap for derive_78b_basis.py: a synthetic kit (built with the builder's test helper fake_kit,
test code only) plus MY trap files with names the builder did not plant; my own audit hook records every open under
the scratch root. Also probes check_path's create-*.json loophole and a forbidden-part path with an allowed name."""
import pathlib, sys, importlib.util

KIT = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-a/runkit/stage1-78b")
SCR = pathlib.Path(sys.argv[1])
opened = []


def hook(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, pathlib.Path)) and str(args[0]).startswith(str(SCR)):
        opened.append(str(args[0]))


sys.addaudithook(hook)
sys.dont_write_bytecode = True
sys.path.insert(0, str(KIT))
import derive_78b_basis as D  # noqa: E402
spec = importlib.util.spec_from_file_location("t78", KIT / "tests" / "test_rules_78b.py")
T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)   # for fake_kit only

root = SCR / "tmp"
kit = T.fake_kit(root, "olmo2-7b", "family-probe-sp-olmo2-7b-trap", "sp-olmo2-7b-7001", traps=False)
kit2 = T.fake_kit(root, "llama31-8b", "family-probe-sp-llama31-8b-trap", "sp-llama31-8b-7001", traps=False)
host = kit / "hosts" / "sp-olmo2-7b-7001"
unit = kit / "retrieved" / "sp-olmo2-7b-7001" / "tree" / "round1" / "1101-a0-e1-a1"
MY_TRAPS = {
    host / "create-secrets.json": '{"token": "VERIFIER-TRAP-A"}',          # matches the create-*.json loophole; must not be opened
    host / "pod.json": '{"text": "VERIFIER-TRAP-B"}',
    host / "orchestrate.jsonl": '{"text": "VERIFIER-TRAP-C"}\n',
    unit / "records.jsonl": '{"text": "VERIFIER-TRAP-D"}\n',
    unit / "steps.jsonl": '{"text": "VERIFIER-TRAP-E"}\n',
    unit / "plan.json": '{"text": "VERIFIER-TRAP-F"}',
    unit / "eval" / "verification.json": '{"text": "VERIFIER-TRAP-G"}',      # an allowed NAME inside a forbidden part
    kit / "retrieved" / "sp-olmo2-7b-7001" / "tree" / "cuda-preflight-1" / "eval-sample" / "generations.jsonl": "VERIFIER-TRAP-H\n",
    kit / "retrieved" / "sp-olmo2-7b-7001" / "tree" / "cuda-preflight-1" / "verification.json": '{"text": "VERIFIER-TRAP-I"}',
    kit / "retrieved" / "sp-olmo2-7b-7001" / "verified.jsonl": '{"text": "VERIFIER-TRAP-J"}\n',
    kit / "KIT-README.md": "VERIFIER-TRAP-K\n",
}
for p, txt in MY_TRAPS.items():
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(txt)
opened.clear()
basis = D.derive(root, kits={"olmo2-7b": ("family-probe-sp-olmo2-7b-trap",), "llama31-8b": ("family-probe-sp-llama31-8b-trap",)})
names = sorted({pathlib.Path(p).name for p in opened})
hit = [str(pathlib.Path(p).relative_to(root)) for p in opened if pathlib.Path(p) in MY_TRAPS]
text = D.canonical(basis).decode()
print("opens:", len(opened), "distinct names:", names)
print("my traps opened:", hit)
print("trap text in output:", "VERIFIER-TRAP" in text)
# the gate itself on my traps
refused = 0
for p in MY_TRAPS:
    try:
        D.check_path(p); print("  check_path ALLOWS:", str(p.relative_to(root)))
    except D.RecordRefused:
        refused += 1
print(f"check_path refused {refused} of {len(MY_TRAPS)} trap paths (the create-*.json one is the known loophole)")
ok = not hit and "VERIFIER-TRAP" not in text and all(n in D.ALLOWED_NAMES for n in names)
print("TRAP TEST", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
