"""K2 re-verifier's probe R7: init-block B through the REAL kit_inputs rebuild (no stub): block A run in its own copy,
its part written by record-done, the inputs file by write-blinded-inputs; then a block-B copy in the same repository
records PLAN_B_78B (record-plan-b-78b) and plans block B; an edited inputs file then refuses."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import test_planning_ab_78b as T


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_r7_init_block_b_with_the_real_kit_inputs(tmp_path, monkeypatch):
    fam = "olmo2-7b"
    wa = T.ABWorld(tmp_path, monkeypatch, fam, "A")
    hosts = T.released_a(wa)
    gate_path = wa.repo / wa.r78.GATE_78B["path"]
    blind_pin = dict(wa.tool.SR2_BLINDING_RECORD)
    noise = wa.noise
    for h in hosts:
        T.pull_planted(wa, h)
        wa.tool.record_done(h)
    got = wa.tool.write_blinded_inputs()
    T.close(wa)

    wb = T.ABWorld(tmp_path, monkeypatch, fam, "B")
    wb.n = 500
    wb.pin("GATE_78B", gate_path)
    wb.noise = noise
    monkeypatch.setattr(wb.tool, "SR2_BLINDING_RECORD", blind_pin)
    wb.fill(blinding=False)
    T.n_units(wb)
    s = T.SR2.__new__(T.SR2)
    s.w, s.families = wb, ("olmo2-7b",)
    s.sim("C")
    blinded = wb.record({"df": 12, "inputs_sha256": got["sha256"], "kind": "scale-78b blinded sigma", "sigma_A_pp": 4.0,
                         "version": 1}, "blinded-real.json")
    rec = T.plan_b(wb, blinded)
    assert (rec["plan"], rec["sr2_adopted"]) == ("A", True)
    T.seal_sibling(wb, "A")
    out = wb.init(dry_run=True, blinded=str(blinded))
    assert (out["plan"], out["runs"]) == ("A", 23)
    inputs = wb.tool.BLINDED_INPUTS
    inputs.write_text(inputs.read_text() + " ")
    with pytest.raises(SystemExit, match="blinded_sigma.py's output .* is missing or is not the file|is not the one the kit writes"):
        wb.init(dry_run=True, blinded=str(blinded))
    T.close(wb)
