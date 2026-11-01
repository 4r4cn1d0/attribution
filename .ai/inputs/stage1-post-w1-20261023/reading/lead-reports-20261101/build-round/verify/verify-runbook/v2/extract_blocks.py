"""Extract the runbook's zsh blocks and their Python heredocs; zsh -n each block, ast.parse each heredoc; save the
step 0.2 seal check, the 0.6 manifest writer, the 0.7 ledger pre-check and the step-6 extractor as files."""
import ast, pathlib, re, subprocess, sys
RB = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
text = RB.read_text()
blocks = re.findall(r"```zsh\n(.*?)```", text, flags=re.S)
print("zsh blocks:", len(blocks))
for i, b in enumerate(blocks):
    p = OUT / f"block-{i}.zsh"; p.write_text(b)
    r = subprocess.run(["zsh", "-n", str(p)], capture_output=True, text=True)
    print(f"  block {i}: zsh -n exit {r.returncode} {r.stderr.strip()[:200]}")
heredocs = re.findall(r"<<'EOF'\n(.*?)\nEOF\n", text, flags=re.S)
print("heredocs:", len(heredocs))
names = {}
for i, h in enumerate(heredocs):
    ast.parse(h)
    first = h.splitlines()[0]
    key = ("seal_check" if "blocks = pathlib.Path(sys.argv[1]), sys.argv[2:]" in h and "seals" in h else
           "requirements" if "packages" in h and "--hash=sha256" in h else
           "manifest_writer" if "outside time stamp manifest" in h else
           "ledger_precheck" if "ledgers_named_in_plan" in h else
           "extractor" if "stage1 reading record" in h else f"heredoc-{i}")
    names[key] = h
    (OUT / f"{key}.py").write_text(h + "\n")
    print(f"  heredoc {i}: parses; saved as {key}.py ({len(h.splitlines())} lines)")
