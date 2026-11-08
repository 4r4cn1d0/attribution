"""Re-verifier scratch: the lead's commands in r1-c.md section 5, parsed as written and run in process with cwd = MAIN.
Every list, bank, anchor list and unit folder is replaced by a NONEXISTENT path (pins kept as written), so no real list,
bank, anchor list or unit is opened; the encode count uses the builder's fake codec (no tokenizer is loaded). Prints
exit codes and the refusal text only.

    PY -B CMD_CHECK.py WS MAIN REPORT_MD OUT_DIR
"""
import contextlib
import io
import os
import re
import shlex
import sys
from pathlib import Path

ws, main_root, report, out_dir = map(Path, sys.argv[1:5])
sys.path.insert(0, str(ws))
from scripts.scale78b import encode_count_78b as ec, tau_l_78b as tl          # noqa: E402
from scripts.scale78b.tests import test_encode_count_78b as T                  # noqa: E402

text = report.read_text(encoding="utf-8")
sec = text.split("## 5. Commands for the lead's real runs", 1)[1].split("## 6.", 1)[0]
block = sec.split("```sh", 1)[1].split("```", 1)[0]
joined = re.sub(r"\\\n\s*", " ", block)
commands = [ln.split("#")[0].strip() for ln in joined.splitlines() if ln.strip().startswith("sandbox-exec")]
NONE = "/nonexistent-reverify"
subst = {"<S1_JSON>": f"{NONE}/s1.json", "<S3_SAFE_POOL_JSON>": f"{NONE}/s3_safe.pool.json",
         "<S4_CANDIDATES_JSON>": f"{NONE}/s4_candidates.json", "<OEXT_BANK_JSON>": f"{NONE}/oext_bank.json",
         "<ANCHOR_PROMPT_LIST_JSON>": f"{NONE}/anchor_prompts.json", "<F>": "olmo2-7b",
         "<P_F>": "prepared-kt-dolly-olmo2", "<N_A0_1103_UNIT_FOLDER>": f"{NONE}/n-a0-1103",
         "<ITS_COMPLETE_JSON_SHA256>": "a" * 64}
os.chdir(main_root)
n = 0
for cmd in commands:
    words = shlex.split(cmd)
    if not any(w.endswith(("encode_count_78b.py", "tau_l_78b.py")) for w in words):
        continue
    n += 1
    i = next(k for k, w in enumerate(words) if w.endswith(".py"))
    script, argv = words[i], words[i + 1:]
    pre = words[:i]
    argv2 = []
    for a in argv:
        for k, v in subst.items():
            a = a.replace(k, v)
        a = a.replace("$OUT", str(out_dir / f"c{n}"))
        if script.endswith("tau_l_78b.py") and re.match(r"^11\d\d=tmp/", a):     # a real unit folder: replaced
            seed, rest = a.split("=", 1)
            a = f"{seed}={NONE}/unit-{seed}:{rest.rpartition(':')[2]}"
        argv2.append(a)
    (out_dir / f"c{n}").mkdir(parents=True, exist_ok=True)
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        if script.endswith("encode_count_78b.py"):
            code = ec.main(argv2, context=T.fake_context())
        else:
            code = tl.main(argv2)
    print(f"[{n}] {script} pre={pre[:2]}+{pre[2:]!r:.40} flags={[a for a in argv if a.startswith('--')]}")
    print(f"     exit {code}; stderr: {err.getvalue().strip()[:230]}")
    print(f"     wrote: {sorted(p.name for p in (out_dir / f'c{n}').iterdir())}")
print(n, "tool commands")
