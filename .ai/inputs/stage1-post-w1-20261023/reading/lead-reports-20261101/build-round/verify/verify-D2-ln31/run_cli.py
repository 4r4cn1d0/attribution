"""Run the tool's real command line (scripts.stage1_s1.hlc_draw.__main__.main) in this process, with the pinned
settings whose three external pins are replaced by a synthetic world's (pins file = argv[1]); exit with main's code.

    python -B run_cli.py PINS.json draw|check --kit ... (the tool's own arguments)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib  # noqa: E402

from scripts.stage1_s1.hlc_draw import draw as dr  # noqa: E402
from scripts.stage1_s1.hlc_draw.__main__ import main  # noqa: E402

pins = json.loads(Path(sys.argv[1]).read_text())
dr._SETTINGS = vlib.cfg_for(pins)
sys.exit(main(sys.argv[2:]))
