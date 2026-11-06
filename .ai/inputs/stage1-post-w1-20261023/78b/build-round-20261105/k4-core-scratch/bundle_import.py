"""Build a bundle-like tree (engine files as pack_setup.engine_files lists them + stage1_rules.SCORER_PINS files only),
then import the wrapper and the 9 1B modules from it in a fresh -I process. Reads code only."""
import ast, importlib.util, pathlib, shutil, subprocess, sys
repo, out, py = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
kit = repo / "runkit/stage1-78b"
src = (kit / "stage1_rules.py").read_text(); env = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and \
            node.targets[0].id in ("WRAPPER", "ANCHOR_SCRIPT", "SCORER_SETTINGS", "PINS_78B", "PINS_INDEX", "SCORER_PINS"):
        env[node.targets[0].id] = eval(compile(ast.Expression(node.value), "x", "eval"), {}, env)
ps = (kit / "pack_setup.py").read_text()
pre = [n for n in ast.parse(ps).body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "PREFLIGHT_SCRIPTS"]
preflight = eval(compile(ast.Expression(pre[0].value), "x", "eval")) if pre else ()
files = []
for comp in ("minimal_safety", "safety_selection"):
    for f in (repo / "experiments" / comp).rglob("*"):
        if f.is_file() and not f.is_symlink() and "__pycache__" not in f.parts and f.suffix in {".py", ".json", ".md", ".lock"}:
            files.append(f.relative_to(repo))
files += [pathlib.Path("scripts") / n for n in preflight] + [pathlib.Path(p) for p in env["SCORER_PINS"]]
out.mkdir(parents=True)
for rel in files:
    (out / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(repo / rel, out / rel)
mods = ["scripts.scale78b.scorers_78b"] + [f"scripts.stage1.{m}" for m in ("s1common", "make_untuned_answers",
        "representation_pass", "score_l1_larf", "score_classifier", "score_s3_datarx", "write_score_edit",
        "write_add_edit", "build_s_pool", "lexicon_pin", "token_accounting")]
code = ("import sys, importlib; sys.path.insert(0, %r); ok = []\n"
        "for m in %r:\n    importlib.import_module(m); ok.append(m)\n"
        "import scripts.scale78b.scorers_78b as w\n"
        "print('imported', len(ok)); print('kinds', sorted(w.KINDS))\n") % (str(out), mods)
r = subprocess.run([py, "-I", "-B", "-c", code], cwd=str(out.parent), capture_output=True, text=True,
                   env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HF_HUB_OFFLINE": "1"})
print("files", len(files), "exit", r.returncode); print(r.stdout[-800:]); print(r.stderr[-1500:])
