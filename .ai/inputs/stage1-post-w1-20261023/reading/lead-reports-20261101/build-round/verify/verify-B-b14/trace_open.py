"""Run overlap_inputs.main(argv) under an audit hook; print every file path opened or listed under ROOT (synthetic
worlds only). Usage: python -B trace_open.py WS ROOT -- <writer args>"""
import json
import os
import sys

ws, root = sys.argv[1], os.path.realpath(sys.argv[2])
argv = sys.argv[sys.argv.index("--") + 1:]
sys.path.insert(0, ws)
events = []


def hook(event, args):
    if event in ("open", "os.listdir", "os.scandir", "os.walk", "glob.glob"):
        path = args[0] if args else None
        if isinstance(path, (str, bytes, os.PathLike)):
            p = os.fsdecode(path)
            real = os.path.realpath(p) if os.path.exists(p) else p
            if real.startswith(root + os.sep):
                mode = args[1] if event == "open" and len(args) > 1 else ""
                events.append((event, os.path.relpath(real, root), str(mode)))


from scripts.stage1_s1 import overlap_inputs as oi  # noqa: E402  (imports before the hook: not traced)

sys.addaudithook(hook)
code = oi.main(argv)
print(json.dumps({"exit": code, "events": events}))
