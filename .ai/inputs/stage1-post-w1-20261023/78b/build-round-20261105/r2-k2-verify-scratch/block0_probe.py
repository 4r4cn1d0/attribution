"""Verifier probe (K2V): block 0's behaviour in one kit tree, every new pin null. Prints a JSON summary of the dry-run
and real init printouts and returns, plan.json bytes (tmp path normalised, clock fixed), the operator log, deal 0 and
a second release. Usage: python -B block0_probe.py KIT_DIR OUT_DIR"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

import pytest

kit = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
tests = kit / "tests"
sys.path.insert(0, str(tests))
spec = importlib.util.spec_from_file_location("test_stage1_runkit", tests / "test_stage1_runkit.py")
rk = importlib.util.module_from_spec(spec)
sys.modules["test_stage1_runkit"] = rk
spec.loader.exec_module(rk)
assert rk.KIT.resolve() == kit, (rk.KIT, kit)

result = {}
for family in ("olmo2-7b", "llama31-8b"):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / family
        root.mkdir()
        with pytest.MonkeyPatch.context() as mp:
            w = rk.World(root, mp, family)
            mp.setattr(w.mac, "utc", lambda: "2026-11-08T00:00:00+00:00")
            r = {}
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                dry = w.init(dry_run=True)
            r["dry_stdout"] = buf.getvalue().replace(str(root), "<TMP>")
            r["dry_return"] = json.loads(json.dumps(dry, default=str).replace(str(root), "<TMP>"))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                got = w.init()
            r["init_stdout"] = buf.getvalue().replace(str(root), "<TMP>")
            r["init_return"] = json.loads(json.dumps(got, default=str).replace(str(root), "<TMP>"))
            data = (w.root / "plan.json").read_bytes().replace(str(root).encode(), b"<TMP>")
            (out_dir / f"plan-{family}.json").write_bytes(data)
            r["plan_len_sha"] = [len(data), hashlib.sha256(data).hexdigest()]
            ops = w.root / "operator-actions.jsonl"
            r["ops"] = [json.loads(x) for x in ops.read_text().splitlines()] if ops.is_file() else None
            for op in r["ops"] or []:
                op.pop("utc", None)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                try:
                    r["deal0"] = w.tool.deal_command("0", [])
                except SystemExit as exc:
                    r["deal0"] = f"SystemExit: {exc}"
            try:
                w.tool.release("0")
                r["release_again"] = "released"
            except SystemExit as exc:
                r["release_again"] = f"SystemExit: {exc}"
            # the null pins this round added, as the kit holds them
            pins = {}
            for name in ("GATE_78B", "PLAN_B_78B", "W1_18_78B"):
                pins[name] = getattr(w.r78, name, "absent")
            for name in ("BRANCH_78B", "ANCHOR_STOP", "N_UNITS"):
                pins[name] = getattr(w.r78, name, "absent")
            for name in ("SR2_BLINDING_RECORD", "S4_DOSES_RECORD", "PADDED_TOKENS_78B", "SR2_SIMULATION_REDUCED"):
                pins[name] = getattr(w.tool, name, "absent")
            r["pins"] = pins
            for name in rk.MODULES:
                sys.modules.pop(name, None)
        result[family] = r
(out_dir / "summary.json").write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + "\n")
print(json.dumps({f: r["plan_len_sha"] for f, r in result.items()}))
