"""Scratch check (not a project test): run legitimate synthetic study shapes that the package tests do
not route through study_evidence, and confirm the fifth candidate neither falsely refuses them
(snapshot check, require_attempts) nor labels a block whose last session lost its end record complete.
ENGINEERING FIXTURE only; nothing here is a scientific result."""

from __future__ import annotations

import copy
import dataclasses
import shutil
import sys
import tempfile
from pathlib import Path

WS = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(WS), str(WS / "experiments" / "safety_selection" / "tests")]

from experiments.safety_decision_policy.common import RequestRefused, VerificationError, canonical_json, read_json_strict  # noqa: E402
from experiments.safety_decision_policy.analysis import analyze  # noqa: E402
from experiments.safety_decision_policy.controller import Study, study_evidence  # noqa: E402
from experiments.safety_decision_policy.synthetic import FakeBackend, make_world, prepare_synthetic  # noqa: E402

CONFIGS = WS / "experiments" / "safety_decision_policy" / "configs"
METHODS = ("S-", "S+")
OUT = Path(tempfile.mkdtemp(prefix="adv-", dir=sys.argv[2]))
world = make_world()
setup = prepare_synthetic(OUT / "dev", world, template=read_json_strict(CONFIGS / "example-engineering.json"),
                          spec=read_json_strict(CONFIGS / "example-dev-fit-spec.json"))
z0 = setup["config"]["blocks"]["list"][0]["selector_seed_start"]
final_seed = setup["config"]["blocks"]["list"][0]["final_seed"]


def study(root, *, config=None, backend=None, **changes):
    w = dataclasses.replace(world, **changes) if changes else world
    b = backend or FakeBackend(w)
    return Study(root, config=config or setup["config"], record=setup["record"], backend=b, recipe=setup["recipe"],
                 data_config=setup["data_config"], shape=w.shape("heldout"), actual_pins=setup["pins"],
                 process_start=b.clock(), engineering_fixture=True), b


def run(root, block=0, expect=None, **kw):
    s, b = study(root, **kw)
    try:
        if expect:
            try:
                s.run_block(block)
            except expect:
                return None
            raise AssertionError(f"expected {expect}")
        return s.run_block(block)
    finally:
        s.close()


class Steps(FakeBackend):
    """Controller-side fake time (nonzero segments everywhere)."""

    def verify(self, receipt, spec):
        self.now += 1.5
        return super().verify(receipt, spec)

    def evaluation(self, receipt, spec):
        self.now += 2.5
        return super().evaluation(receipt, spec)


def check(name, root, config=None, expect_complete_blocks=(), expect_lower=()):
    config = config or setup["config"]
    try:
        ev = study_evidence(root, config)
    except VerificationError as exc:
        print(f"FAIL  {name}: study_evidence refused a legitimate tree: {exc}")
        return False
    report = analyze(ev["results"], config, ev["static"], ev["started"], recorded=ev["recorded"])
    ok = True
    for block, rec in ev["recorded"].items():
        snap = next(r for r in ev["results"] if r["block"] == block)["costs"]
        if rec["result_status"] != "aborted":
            for key, field in (("actual", "total_seconds"), ("selection_plus_chosen_model", "seconds")):
                for m in METHODS:
                    if rec[key][m][field] != snap[key][m][field] and rec["snapshot"]["compared"]:
                        print(f"FAIL  {name}: block {block} {key} {m} differs from snapshot")
                        ok = False
        complete = rec["physical"]["timing_complete"]
        if block in expect_complete_blocks and not complete:
            print(f"FAIL  {name}: block {block} physical unexpectedly incomplete: {rec['physical']['incomplete_because']}")
            ok = False
        if block in expect_lower and complete:
            print(f"FAIL  {name}: block {block} physical labelled complete despite a missing end record")
            ok = False
        if rec["physical"]["seconds"] < snap["physical"]["seconds"] and rec["snapshot"]["compared"]:
            print(f"FAIL  {name}: block {block} recorded physical below snapshot")
            ok = False
    entries = {e["block"]: e for e in report["costs"]["per_block"]}
    for block in expect_lower:
        if entries[block].get("cost_margin") is not None and entries[block]["status"] != "aborted":
            sub = entries[block].get("selection_plus_chosen_model_seconds_are", {})
            if sub != {"S-": "complete", "S+": "complete"}:
                print(f"FAIL  {name}: block {block} has a margin with lower-bound subtotals")
                ok = False
    print(("ok    " if ok else "FAIL  ") + f"{name}: blocks {sorted(ev['recorded'])} recorded, "
          f"started {sorted(ev['started'])}, physical total {report['costs']['physical_controller_seconds']}")
    return ok


results = []

# 1. two blocks in one process (block 1 shared: unmeasured setup), with controller time everywhere
root = OUT / "shared"
s, b = study(root, backend=Steps(world))
s.run_block(0); s.run_block(1); s.close()
results.append(check("two blocks, one process, controller time", root, expect_complete_blocks=(0,)))

# 2. final-incomplete block
root = OUT / "final-incomplete"
assert run(root, final_failures=frozenset({"a0"}))["status"] == "final-incomplete"
results.append(check("final-incomplete", root, expect_complete_blocks=(0,)))

# 3. identical choices (every edit infeasible), sensitivity on
config = copy.deepcopy(setup["config"]); config["constraints"]["tau_utility_loss"] = -1.0
root = OUT / "identical"
run(root, config=config)
results.append(check("identical choices", root, config=config, expect_complete_blocks=(0,)))

# 4. screen abort
edit = sorted(world.groups["heldout"])[0]
root = OUT / "abort"
assert run(root, failures=frozenset({(f"screen-{edit}-{z0}", 1), (f"screen-{edit}-{z0}", 2)}))["status"] == "aborted"
results.append(check("screen abort", root, expect_complete_blocks=(0,)))

# 5. KeyboardInterrupt mid-acquisition, resumed to completion (two sessions, both ended)
first = None
probe = OUT / "probe"
run(probe)
import json  # noqa: E402
first = json.loads((probe / "blocks" / "0" / "plan-S-.json").read_text())["transcript"]["purchases"][0]["ops"][0]
root = OUT / "interrupted-resumed"
run(root, expect=KeyboardInterrupt, backend=Steps(dataclasses.replace(world, interrupts=frozenset({(first, 1)}))))
run(root, backend=Steps(world))
results.append(check("interrupted then resumed", root, expect_complete_blocks=(0,)))

# 6. refusal then resumed
root = OUT / "refused-resumed"
run(root, expect=RequestRefused, refusals=frozenset({(f"screen-a0-{z0}", 1)}))
run(root)
results.append(check("refusal then resumed", root, expect_complete_blocks=(0,)))

# 7. hard kill: attempt without receipt and session 1 without end record, then resumed to a result
root = OUT / "hard-kill"
run(root, expect=KeyboardInterrupt, backend=Steps(dataclasses.replace(world, interrupts=frozenset({(first, 1)}))))
(root / "blocks/0/ops" / first / "attempt-1" / "receipt.json").unlink()
(root / "blocks/0/sessions/session-1-end.json").unlink()
run(root, backend=Steps(world))
results.append(check("hard kill then resumed (session 1 unknown)", root, expect_lower=(0,)))

# 8. F2 on a multi-session block: the result-writing session (2) lost its end record
root = OUT / "f2-multisession"
shutil.copytree(OUT / "interrupted-resumed", root)
(root / "blocks/0/sessions/session-2-end.json").unlink()
results.append(check("result-writing session 2 lost its end record", root, expect_lower=(0,)))

# 9. an EARLIER session's end record deleted after the result: refusal expected (documented open decision 15)
root = OUT / "earlier-end-deleted"
shutil.copytree(OUT / "interrupted-resumed", root)
(root / "blocks/0/sessions/session-1-end.json").unlink()
try:
    study_evidence(root, setup["config"])
    print("NOTE  earlier end record deleted after the result: NOT refused (snapshot saw it)")
except VerificationError as exc:
    print(f"ok    earlier end record deleted after the result: refused as documented ({str(exc)[:90]}...)")

# 10. a block started without a result beside a complete one (analysis mixes recorded and started)
root = OUT / "mixed"
s, b = study(root)
s.run_block(0); s.close()
run(root, block=1, expect=KeyboardInterrupt, backend=FakeBackend(dataclasses.replace(
    world, interrupts=frozenset({(f"screen-a0-{setup['config']['blocks']['list'][1]['selector_seed_start']}", 1)}))))
results.append(check("complete block beside a started one", root, expect_complete_blocks=(0,)))

print(f"\n{sum(results)}/{len(results)} scenario checks passed; scratch trees under {OUT}")
sys.exit(0 if all(results) else 1)
