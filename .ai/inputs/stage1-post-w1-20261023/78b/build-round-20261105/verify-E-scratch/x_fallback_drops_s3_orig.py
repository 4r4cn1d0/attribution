"""Verifier check X3: what the unchanged 1B make_untuned_answers.run() writes when the S4 keep target is NOT reached
(the 7-8B dose fallback) and the s3 list runs in the same call. Counts and file names only; no text printed.
Run: cd <ws-e>; <main venv python> -B x_fallback_drops_s3_orig.py"""
import json
import sys
import tempfile
from pathlib import Path

W = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-e")
for extra in (W, W / "scripts" / "stage1" / "tests", W / "experiments" / "safety_selection" / "tests"):
    sys.path.insert(0, str(extra))

import ss_fixtures as sfx  # noqa: E402
import test_make_untuned_answers as tmua  # noqa: E402
from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import make_untuned_answers as mua  # noqa: E402

SCRATCH = Path(__file__).resolve().parent
root = Path(tempfile.mkdtemp(prefix="x3-", dir=SCRATCH))
rec = sfx.recipe(**{"generation.batch_size": 4})
(root / "rec.json").write_text(json.dumps(rec))
(root / "s.json").write_text(json.dumps(rec))


def plist(name, n):
    items = [{"id": f"c-{i:03d}", "prompt": f"Synthetic question {i}: how are tides measured in harbour {i % 7}?"} for i in range(n)]
    data = canonical_json({"kind": "stage1 prompt list", "version": 1, "name": name, "items": items})
    p = root / f"{name}.json"
    p.write_bytes(data)
    return (p, sha256_bytes(data))


s4, s3 = plist("s4", 40), plist("s3", 10)
for keep in (30, 6):   # 30 is unreachable with the 1B FakeGenerator (about 1 in 3 refuses) on 40 prompts; 6 is reachable
    settings = tmua.settings_for(rec, keep=keep, s3_size=10)
    files, code = mua.run(rec_path=root / "rec.json", s_path=root / "s.json", lists={"s4": s4, "s3": s3}, losses={},
                          loaders=sfx.fixture_loaders(), settings=settings, settings_sha256="e" * 64,
                          generate=tmua.FakeGenerator(sfx.fixture_codec()))
    record = json.loads(files[mua.RECORD])
    print(f"keep={keep}: exit {code}; complete {record['complete']}; files {sorted(files)}; "
          f"s4 kept {record['lists']['s4']['kept']} of answered {record['lists']['s4']['answered']}; "
          f"s3 answered {record['lists']['s3']['answered']}; record names s3_orig_pool_sha256: "
          f"{'s3_orig_pool_sha256' in record['lists']['s3']}; s3_orig.pool.json written: {'s3_orig.pool.json' in files}; "
          f"s4.json written: {'s4.json' in files}")
