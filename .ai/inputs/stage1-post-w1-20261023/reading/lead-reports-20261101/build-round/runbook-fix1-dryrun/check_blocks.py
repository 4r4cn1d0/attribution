"""Extract every <<'EOF' heredoc from a file and ast.parse it; extract every ```zsh block of a Markdown file and zsh -n it."""
import ast, re, subprocess, sys, pathlib, tempfile
path = pathlib.Path(sys.argv[1]); text = path.read_text()
heredocs = re.findall(r"<<'EOF'\n(.*?)\nEOF\n", text, flags=re.S)
for i, body in enumerate(heredocs):
    ast.parse(body)
print(f"{path.name}: {len(heredocs)} heredocs parse")
if path.suffix == ".md":
    blocks = re.findall(r"```zsh\n(.*?)\n```", text, flags=re.S)
    bad = 0
    for i, b in enumerate(blocks):
        with tempfile.NamedTemporaryFile("w", suffix=".zsh", delete=False, dir=sys.argv[2]) as f:
            f.write(b + "\n"); name = f.name
        r = subprocess.run(["zsh", "-n", name], capture_output=True, text=True)
        if r.returncode:
            bad += 1; print("block", i, "zsh -n failed:", r.stderr.strip()[:300])
        pathlib.Path(name).unlink()
    print(f"{path.name}: {len(blocks)} zsh blocks, {bad} failed zsh -n")
