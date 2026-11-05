"""Verifier's inspection of the Llama S1 set (hashes, ids, counts only; no text printed).
Usage: <main venv> -I -B inspect_s1_llama3.py <repo copy>"""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO))
from experiments.safety_selection.common import sha256_bytes, canonical_json  # noqa: E402
from experiments.safety_selection.edits import EditError, parse_edit  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import write_add_edit as wae  # noqa: E402

SET = REPO / ".ai/inputs/scale-78b-s1-llama3-20261105"
OUT = SET / "out"
EDIT = REPO / "tmp/scale-78b-s1-llama3-20261105/edits/add_s1.json"
LIST = REPO / "tmp/scale-78b-s1-llama3-20261105/list/s1.json"
OLMO_EDIT = Path("/Users/spiderishi/Coding/attribution/tmp/stage1-olmo/retrieved/a-3/tree/round1/"
                 "1103-edit-904a0cf1ef9b09c54dbf215384e61fd3360195f2fc0557ecb951b9e7d5dc2d10-e1-a1/edit.json")
RECORD = REPO / ".ai/inputs/stage1-commitments-20261016/add-s1/add_edit_record.json"
LLAMA = REPO / "tmp/kt-prepared/prepared-kt-dolly-llama3"
OLMO = REPO / "tmp/kt-prepared/prepared-kt-dolly-olmo2"
LLAMA_M = "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"
OLMO_M = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
LIST_PIN = "389c20ad00261b1a304d3dd9f14a113a0b05bcec63758262af1b1629d48e0480"


def h(b): return hashlib.sha256(b).hexdigest()


def dump(o, pre="", limit=120):
    if isinstance(o, dict):
        for k, v in o.items():
            dump(v, f"{pre}.{k}", limit)
    elif isinstance(o, list):
        print(f"{pre}: list[{len(o)}]")
        if o and not isinstance(o[0], (dict, list)):
            print(f"{pre}[0]: {type(o[0]).__name__} len {len(str(o[0]))}")
        elif o:
            dump(o[0], f"{pre}[0]", limit)
    else:
        s = str(o)
        print(f"{pre}: {type(o).__name__} {s if len(s) <= limit else s[:limit] + '...(' + str(len(s)) + ')'}")


manifest = json.loads(OUT.joinpath("MANIFEST.json").read_bytes())
record = json.loads(OUT.joinpath("add_edit_record.json").read_bytes())
settings = json.loads(OUT.joinpath("write_add_edit_llama3.settings.json").read_bytes())
print("== MANIFEST (rows and files abbreviated) ==")
dump({k: v for k, v in manifest.items() if k != "rows"})
print("rows:", len(manifest["rows"]))
print()
print("== script hash check ==")
script_sha = h((SET / "build_s1_llama3.py").read_bytes())
print("file     ", script_sha)
print("MANIFEST ", manifest["script"]["sha256"], "EQUAL" if script_sha == manifest["script"]["sha256"] else "DIFFERS")
print("settings.derived_from.by_sha256", settings["derived_from"]["by_sha256"], "EQUAL" if settings["derived_from"]["by_sha256"] == script_sha else "DIFFERS")
print("record sha", h(OUT.joinpath("add_edit_record.json").read_bytes()), "MANIFEST", manifest["record"]["sha256"])
print("settings sha", h(OUT.joinpath("write_add_edit_llama3.settings.json").read_bytes()), "MANIFEST", manifest["settings"]["sha256"],
      "record.provenance", record["provenance"]["settings_sha256"])
print("edit sha", h(EDIT.read_bytes()), "MANIFEST files[0]", manifest["files"][0]["sha256"], "record edits[0]", record["edits"][0]["sha256"])
print("list sha", h(LIST.read_bytes()), "pin", LIST_PIN)
print()
print("== rows: ids and order vs the committed OLMo record ==")
committed = json.loads(RECORD.read_bytes())
print("committed record sha", h(RECORD.read_bytes()))
m_add = [r["add_id"] for r in manifest["rows"]]
m_list = [r["list_id"] for r in manifest["rows"]]
c_add = [r["add_id"] for r in committed["rows"]]
c_list = [r["list_id"] for r in committed["rows"]]
print("add ids == add-s1-001..048:", m_add == [f"add-s1-{j:03d}" for j in range(1, 49)])
print("add ids equal committed:", m_add == c_add, "; list ids equal committed (same order):", m_list == c_list)
print("manifest rows == record rows:", manifest["rows"] == record["rows"])
m_pt = [r["prompt_tokens"] for r in manifest["rows"]]
m_tt = [r["target_tokens"] for r in manifest["rows"]]
c_pt = [r["prompt_tokens"] for r in committed["rows"]]
c_tt = [r["target_tokens"] for r in committed["rows"]]
print("prompt tokens sum llama", sum(m_pt), "olmo", sum(c_pt), "; per-row equal count", sum(a == b for a, b in zip(m_pt, c_pt)))
print("target tokens sum llama", sum(m_tt), "olmo", sum(c_tt), "; per-row equal count", sum(a == b for a, b in zip(m_tt, c_tt)))
print("prompt - target per row: llama min/max", min(a - b for a, b in zip(m_pt, c_pt)), max(a - b for a, b in zip(m_pt, c_pt)))
print("longest llama row (p+t+1)", max(p + t + 1 for p, t in zip(m_pt, m_tt)), "max_train_tokens", record["max_train_tokens"])
print()
print("== parse_edit: accept on Llama, refuse on OLMo; same rows as the OLMo edit by text hash ==")
data = EDIT.read_bytes()
llama_stub = s1.PreparedView(LLAMA, LLAMA_M).engine_stub()
olmo_stub = s1.PreparedView(OLMO, OLMO_M).engine_stub()
e = parse_edit(data, llama_stub)
print("llama: added", len(e.added), "removed", len(e.removed), "rewrite", len(e.rewrite) if e.rewrite else 0, "arm", e.arm, "manifest", e.document["manifest_sha256"][:8])
try:
    parse_edit(data, olmo_stub)
    print("olmo: ACCEPTED (defect)")
except EditError as exc:
    print("olmo: refused", type(exc).__name__)
od = OLMO_EDIT.read_bytes()
print("olmo edit sha", h(od))
oe = parse_edit(od, olmo_stub)
try:
    parse_edit(od, llama_stub)
    print("olmo edit on llama: ACCEPTED (unexpected)")
except EditError as exc:
    print("olmo edit on llama: refused", type(exc).__name__)
l_rows = sorted(e.added)
o_rows = sorted(oe.added)
print("sorted add ids equal:", [a for a, _, _ in l_rows] == [a for a, _, _ in o_rows])
l_h = [h((p + "\x00" + r).encode()) for _, p, r in l_rows]
o_h = [h((p + "\x00" + r).encode()) for _, p, r in o_rows]
print("per-row (prompt,response) hashes equal, in order:", l_h == o_h, "; count equal", sum(a == b for a, b in zip(l_h, o_h)), "of", len(l_h))
print("edit document keys:", sorted(e.document.keys()))
print("provenance keys:", sorted(e.document["provenance"].keys()))
print("provenance.script", e.document["provenance"].get("script"), e.document["provenance"].get("script_sha256", "")[:12])
print("provenance.inputs", e.document["provenance"].get("inputs"))
print("provenance python/numpy", e.document["provenance"].get("python"), e.document["provenance"].get("numpy"))
print("olmo provenance.inputs", oe.document["provenance"].get("inputs"))
print()
print("== the list: REQ-7 read_list by the pin; independent recovery from the OLMo edit ==")
listing = wae.read_list(LIST, LIST_PIN)
print("list name", listing["name"], "items", len(listing["items"]))
print("list ids == manifest list ids:", [i["id"] for i in listing["items"]] == m_list)
list_id = {r["add_id"]: r["list_id"] for r in committed["rows"]}
doc = canonical_json({"kind": "stage1 prompt list", "version": 1, "name": "s1",
                      "items": [{"id": list_id[a], "prompt": p, "response": r} for a, p, r in o_rows]})
print("independent recovery sha", h(doc), "EQUAL to pin" if h(doc) == LIST_PIN else "DIFFERS from pin", "bytes", len(doc))
print()
print("== text-free check of every committed file and the builder's report/scratch ==")
texts = [t for item in listing["items"] for t in (item["prompt"], item["response"])]
targets = [OUT / "MANIFEST.json", OUT / "add_edit_record.json", OUT / "write_add_edit_llama3.settings.json",
           SET / "README.md", SET / "build_s1_llama3.py", SET / "tests/test_build_s1_llama3.py", SET / "tests/conftest.py",
           REPO / "scripts/scale78b/fingerprint_compare.py", REPO / "scripts/scale78b/s1_olmo2_7b_check.py",
           REPO / "scripts/scale78b/tests/test_fingerprint_compare.py", REPO / "scripts/scale78b/tests/test_noise_reading_rv2_2.py",
           REPO / "scripts/scale78b/tests/test_s1_olmo2_7b_check.py"]
for p in targets:
    print(f"  hits {s1._text_hits(p.read_bytes(), texts):3d}  {p.relative_to(REPO)}")
reports = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/"
               "b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/reports")
for p in sorted([reports / "build-F.md", *[q for q in (reports / "build-F-scratch").rglob("*") if q.is_file()]]):
    print(f"  hits {s1._text_hits(p.read_bytes(), texts):3d}  {p.relative_to(reports)}")
print("edit hits", s1._text_hits(data, texts), "list hits", s1._text_hits(LIST.read_bytes(), texts), "(text-bearing, under tmp)")
print()
print("== settings vs REQ-7's committed settings ==")
base = json.loads((REPO / "scripts/stage1/settings/write_add_edit.json").read_bytes())
changed = sorted(k for k in set(base) | set(settings) if base.get(k) != settings.get(k))
print("changed keys:", changed)
print("labels_sha256 equal to REQ-7's:", base.get("labels_sha256") == settings.get("labels_sha256"))
print("engine_x", settings.get("engine_x", "")[:12], "lists", {k: v.get("rows") for k, v in settings.get("lists", {}).items()})
