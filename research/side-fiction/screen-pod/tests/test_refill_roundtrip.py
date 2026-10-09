"""The full round trip with the real refill tool (slow; run with SCREEN_SLOW=1): round-1 per-row files from a fake-judge
launch and summarize -> sf_screen.py refill (round 2) -> the screen's round-2 plan reads refill-r2.jsonl and its report
-> a fake-judge round-2 launch and summarize -> sf_screen.py finalize accepts the round-2 labels. Everything is written
under the test's tmp_path; sf_screen.py never writes inside tmp/side-fiction/out (it refuses)."""
from __future__ import annotations

import json
import os
import subprocess

import pytest
from conftest import P, SP, SB, FakeGranite, FakeHost, ka_label_map, launch_with, needs_real, sha

SLOW = os.environ.get("SCREEN_SLOW") == "1"
DROPS = {("dark", 7): "Yes", ("dark", 1234): "invalid", ("light", 10): "Yes"}


def sf(*args, timeout=1800):
    env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "HOME": os.environ.get("HOME", "/tmp"),
           "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    import sys
    return subprocess.run([sys.executable, "-I", "-B", str(P.REFILL_TOOL), *args], capture_output=True, text=True,
                          env=env, timeout=timeout, cwd="/")


@needs_real
@pytest.mark.skipif(not SLOW, reason="slow (the refill tool rebuilds all 10,000 rows): set SCREEN_SLOW=1")
def test_round1_to_refill_to_round2_to_finalize(tmp_path, monkeypatch):
    code, host, log, result, folder = launch_with(tmp_path, monkeypatch)
    assert code == 0
    screen = tmp_path / "screen"
    assert SP.main(["summarize", "--from", str(folder), "--out", str(screen)]) == 0
    for arm in ("dark", "light"):                         # three drops in all, as sf_screen's own scenario A
        path = screen / f"round1-{arm}.jsonl"
        rows = [json.loads(x) for x in path.read_bytes().split(b"\n") if x.strip()]
        for r in rows:
            r["granite_harm"] = DROPS.get((arm, r["line"]), "No")
            r["drop"] = r["granite_harm"] != "No"
        path.write_bytes(b"".join(json.dumps(r, sort_keys=True).encode() + b"\n" for r in rows))
    done = sf("refill", "--screen", str(screen / "round1-dark.jsonl"), "--screen", str(screen / "round1-light.jsonl"),
              "--round", "2", "--write-dir", str(screen))
    assert done.returncode == 0, done.stderr[-2000:]
    refill = screen / "refill-r2.jsonl"
    digest = sha(refill.read_bytes())
    planned = SB.plan(2, refill, digest)                    # the screen reads the real tool's refill file
    rows = planned["sources"]["refill"]["rows"]
    assert len(rows) == 15 and {(r.slot_arm, r.slot_line) for r in rows} == set(DROPS)
    assert sorted({r.rank for r in rows}) == [1, 2, 3, 4, 5] and planned["refill"]["script_is_pinned_sf_screen"]
    flagged = ("dark", 7)

    class FlagRank1(FakeHost):                              # dark 7's rank-1 candidate is flagged; all else clean
        def run(self, command, timeout=120, stdin_path=None):
            if "nohup bash" in command:
                bad = {r.response_sha256 for r in rows if (r.slot_arm, r.slot_line) == flagged and r.rank == 1}
                harm = {r.response_sha256: ("yes" if r.response_sha256 in bad else "no") for r in rows}
                self.granite = lambda bundle: FakeGranite(ka_label_map(bundle), harm=harm)
            return super().run(command, timeout, stdin_path)
    monkeypatch.setattr("conftest.FakeHost", FlagRank1)
    import conftest
    code, host, log, result, folder2 = conftest.launch_with(
        tmp_path, monkeypatch, tag="sp-t2", round_=2, extra=("--refill", str(refill), "--refill-sha256", digest))
    assert code == 0
    assert SP.main(["summarize", "--from", str(folder2), "--out", str(screen)]) == 0
    final = tmp_path / "final"
    done = sf("finalize", "--screen", str(screen / "round1-dark.jsonl"), "--screen", str(screen / "round1-light.jsonl"),
              "--screen-refill", str(screen / "round2-refill.jsonl"), "--final-dir", str(final))
    assert done.returncode == 0, done.stderr[-2000:]
    report = json.loads((final / "screen-report.json").read_bytes())
    assert report["arms"]["dark"]["replacement_rank_counts"] == {"1": 1, "2": 1}       # dark 7 took its rank 2
    assert report["arms"]["light"]["replacement_rank_counts"] == {"1": 1}
    assert report["candidate_labels"] == {"no": 14, "yes": 1}
    assert SP.main(["final-reads", "--final-dir", str(final), "--screen-dir", str(screen)]) == 0
    reads = json.loads((screen / "final-reads.json").read_bytes())
    assert reads["rows"] == {"dark": 5000, "light": 5000}
    assert reads["label_sources"] == {"unchanged": 9997, "replacement": 3}
    assert all(sum(b["rows_judged"] for b in reads["arms"][arm]["books"].values()) == 5000 for arm in ("dark", "light"))
    assert set(reads["reads"]) >= {"manipulation_check", "sexual_content_gate", "book_concentration", "shares"}
