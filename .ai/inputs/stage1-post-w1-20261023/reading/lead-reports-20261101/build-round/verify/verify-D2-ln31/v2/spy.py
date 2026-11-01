"""Run the tool's command line (as cli.py) under a Python audit hook that records every file the process opens and
every folder it lists (events open, os.listdir, os.scandir), in order, into OUT (one path per line, with the event).
The hook sits below every Python-level reader (open, io.open, Path.read_bytes, os.open), so no read can bypass it.

    python -B spy.py OUT PINS.json draw|check --kit ... (the tool's own arguments)
"""

import json
import sys
from pathlib import Path

out_path = Path(sys.argv[1])
events = []


def hook(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes)) or event == "open" and args and hasattr(args[0], "__fspath__"):
        events.append(f"open {args[0]}")
    elif event in ("os.listdir", "os.scandir") and args:
        events.append(f"{event} {args[0]}")


sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2lib  # noqa: E402

from scripts.stage1_s1.hlc_draw import draw as dr  # noqa: E402
from scripts.stage1_s1.hlc_draw.__main__ import main  # noqa: E402

pins = json.loads(Path(sys.argv[2]).read_text())
dr._SETTINGS = v2lib.settings_with(pins)
sys.addaudithook(hook)
code = main(sys.argv[3:])
out_path.write_text("\n".join(events) + "\n")
sys.exit(code)
