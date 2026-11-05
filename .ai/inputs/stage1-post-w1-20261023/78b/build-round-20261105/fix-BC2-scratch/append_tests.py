"""Append the second fix round's tests to ws-c's five test files and add the imports they need (exact anchors, each
found once). Prints the files changed and their line counts only."""
import pathlib
import sys

WS = pathlib.Path(sys.argv[1])
S = pathlib.Path(__file__).resolve().parent
PLAN = [
    (WS / ".ai/inputs/scale-78b-sealed-llama3-20261105/tests/test_build_sealed_llama3.py", "add_sealed.py",
     "import json\nimport shutil\n", "import json\nimport os\nimport shutil\n"),
    (WS / "scripts/scale78b/tests/test_build_r_draws_78b.py", "add_rdraws.py",
     "import json\nimport shutil\n", "import json\nimport os\nimport shutil\n"),
    (WS / "scripts/scale78b/tests/test_build_h1_llama3.py", "add_h1.py",
     "import json\nfrom pathlib import Path\n", "import json\nimport os\nfrom pathlib import Path\n"),
    (WS / "scripts/scale78b/tests/test_noise_reading.py", "add_noise.py",
     "import json\nimport math\n", "import hashlib\nimport json\nimport math\n"),
    (WS / "scripts/scale78b/tests/test_make_recipe_s78.py", "add_maker.py", None, None),
]
for path, addition, old, new in PLAN:
    text = path.read_text(encoding="utf-8")
    if old is not None:
        assert text.count(old) == 1, f"{path.name}: import anchor found {text.count(old)} times"
        text = text.replace(old, new)
    extra = (S / addition).read_text(encoding="utf-8")
    assert extra not in text
    if not text.endswith("\n"):
        text += "\n"
    text += extra
    path.write_text(text, encoding="utf-8")
    print(f"{path.relative_to(WS)}: {len(text.splitlines())} lines")
