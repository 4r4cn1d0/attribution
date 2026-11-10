"""K2V probe: orchestrate.w1_18_hold on a released scorer-block O-ext pod with BRANCH_78B pinned (K-8, R-26)."""
import importlib
import json
import pytest
from test_scorer_block_78b import so  # noqa: F401


def test_p8_orchestrate_holds_an_o_only_pod_whose_branch_is_pinned(so, monkeypatch):
    w = so
    w.fill(oext=True)
    assert w.r78.BRANCH_78B[w.family] is not None
    w.pack(("oext_bank", w.oext("bank"), w.sha(w.oext("bank")) if hasattr(w, "sha") else __import__("hashlib").sha256(w.oext("bank").read_bytes()).hexdigest()),
           ("oext_record", w.oext("record"), __import__("hashlib").sha256(w.oext("record").read_bytes()).hexdigest()))
    host = w.init([{"kind": "o_only"}])["released"][0]
    orch = importlib.import_module("orchestrate")
    logged = []
    monkeypatch.setattr(orch, "log", lambda *a, **k: logged.append((a, k)))
    with pytest.raises(SystemExit) as info:
        orch.w1_18_hold(host)
    print("P8 hold:", info.value, logged)
    assert "waits for W1-18's branch record" in str(info.value)
