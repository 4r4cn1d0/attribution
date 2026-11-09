"""K2V probe: block A's blinded_sigma part after a normal deferral (a job deferred on one pod, re-run on another)."""
import json
import pytest
import test_planning_ab_78b as T
from test_planning_ab_78b import wa  # noqa: F401


def test_p9_part_after_a_deferral(wa, capsys):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    first = hosts[0]
    tree = w.root / "retrieved" / first / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    last = done["jobs"][-1]
    last.update(status="deferred", reason="cap")
    last.pop("complete_sha256")
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    outs = {h: w.tool.record_done(h) for h in hosts}
    moved = w.tool.defer(first)
    print("P9 defer ->", moved)
    plan = w.plan()
    new = moved["to"]
    if new not in plan["hosts"]:
        print("P9 release ->", w.tool.release("A"))
    T.pull_planted(w, new)
    out = w.tool.record_done(new)
    print("P9 last record-done ->", {k: v for k, v in out.items() if k != "statuses"}, out["statuses"])
    print("P9 block_complete(A) ->", w.tool.block_complete(w.plan(), "A"), "arms_done ->", w.tool.block_a_arms_done(w.plan()))
    assert "blinded_inputs_part" in out and "path" in out["blinded_inputs_part"], out


def test_p9b_why_the_part_is_not_written(wa):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    first = hosts[0]
    tree = w.root / "retrieved" / first / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    done["jobs"][-1].update(status="deferred", reason="cap")
    done["jobs"][-1].pop("complete_sha256")
    (tree / "JOB-DONE.json").write_text(json.dumps(done))
    for h in hosts:
        w.tool.record_done(h)
    new = w.tool.defer(first)["to"]
    T.pull_planted(w, new)
    w.tool.record_done(new)
    with pytest.raises(SystemExit) as info:
        w.tool.write_blinded_part_command()
    print("P9b write-blinded-part ->", info.value)
    with pytest.raises(SystemExit) as info:
        w.tool.blinded_inputs_part(w.plan(), w.family)
    print("P9b blinded_inputs_part ->", info.value)
    print("P9b moved_hosts ->", w.tool.moved_hosts(w.plan()))
