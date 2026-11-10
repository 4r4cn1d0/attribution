"""Verifier's independent recomputation of the T3 remove lists (track B). Prints ids-free counts, hashes and booleans.

Reads: both prepared sets' manifest.json, engine/groups.json, engine/train_rows.jsonl (row_id and target_tokens only;
the text is dropped at once and never printed); SEAL's edit files and MANIFEST; stage 1's r-draws and record; the
builder's three out/ folders. Loads BLD by path after its SHA-256 check and calls draw_r for d = 1..16 as a cross-check
of my own draw (sha256-derived seed, random.Random(seed).sample(sorted(members), 75), sorted union).
"""
import hashlib, importlib.util, inspect, json, random, sys
from pathlib import Path

WS = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(WS))
from experiments.safety_selection.common import code_identity, canonical_json, derive_seed  # noqa: E402
from experiments.safety_selection.edits import EditError, parse_edit, arm_of  # noqa: E402

FAILS = []
def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def shab(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

# ---- my own readers (ids and counts only) ----
def read_set(root: Path):
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    tokens = {}
    with open(root / "engine/train_rows.jsonl", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            rid, tt = row["row_id"], row["target_tokens"]
            row.clear(); del row
            assert rid not in tokens
            tokens[rid] = tt
    groups = json.loads((root / "engine/groups.json").read_bytes())["partitions"]
    members = {g["group_id"]: sorted(g["members"]) for g in groups["dev"]["groups"]}
    raw_order_sorted = all(g["members"] == sorted(g["members"]) for g in groups["dev"]["groups"])
    cats = {gid: u["category"] for gid, u in manifest["units"].items()}
    return {"manifest_sha": shab(manifest_bytes), "manifest": manifest, "tokens": tokens, "members": members,
            "cats": cats, "heldout_groups": groups["heldout"]["groups"], "raw_sorted": raw_order_sorted,
            "train_sha": sha(root / "engine/train_rows.jsonl"), "groups_sha": sha(root / "engine/groups.json")}

OLMO = read_set(WS / "tmp/kt-prepared/prepared-kt-dolly-olmo2")
LLAMA = read_set(WS / "tmp/kt-prepared/prepared-kt-dolly-llama3")
print(f"olmo manifest {OLMO['manifest_sha']}  llama manifest {LLAMA['manifest_sha']}")
check(OLMO["manifest_sha"] == "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9", "OLMo manifest pin")
check(LLAMA["manifest_sha"] == "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a", "Llama manifest pin")
check(LLAMA["manifest"]["files"]["engine/train_rows.jsonl"] == LLAMA["train_sha"], "Llama manifest lists its train_rows")
check(LLAMA["manifest"]["files"]["engine/groups.json"] == LLAMA["groups_sha"], "Llama manifest lists its groups.json")
check(OLMO["manifest"]["files"]["engine/train_rows.jsonl"] == OLMO["train_sha"], "OLMo manifest lists its train_rows")
check(sorted(OLMO["members"]) == sorted(LLAMA["members"]) and len(OLMO["members"]) == 8, "same 8 group ids")
check(all(OLMO["members"][g] == LLAMA["members"][g] for g in OLMO["members"]), "same sorted member lists")
check(all(len(LLAMA["members"][g]) == 600 for g in LLAMA["members"]), "600 members per unit (Llama)")
check(OLMO["cats"] == LLAMA["cats"], "same categories")
check(set(OLMO["tokens"]) == set(LLAMA["tokens"]) and len(LLAMA["tokens"]) == 4800, "same 4800 row ids")
check(OLMO["heldout_groups"] == [] and LLAMA["heldout_groups"] == [], "held-out empty in both")
check(set().union(*LLAMA["members"].values()) == set(LLAMA["tokens"]), "units partition the Llama rows")
ndiff = sum(1 for r in OLMO["tokens"] if OLMO["tokens"][r] != LLAMA["tokens"][r])
print(f"rows whose target_tokens differ between the sets: {ndiff}")
check(ndiff == 100, "100 rows differ in target_tokens (builder's count)")
print(f"groups.json raw member order sorted? olmo={OLMO['raw_sorted']} llama={LLAMA['raw_sorted']}; groups.json byte-equal? {OLMO['groups_sha'] == LLAMA['groups_sha']}")

# ---- my own draw ----
DESIGN, STREAM = 20261008, "gate-b-random-removal-v1"
def my_seed(*parts):
    return int.from_bytes(hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()[:8], "big")
def my_draw(members, d):
    rows, seeds = [], []
    for gid in sorted(members):
        s = my_seed(DESIGN, STREAM, d, gid)
        rows.extend(random.Random(s).sample(sorted(members[gid]), 75))
        seeds.append(s)
    assert len(set(rows)) == 600
    return sorted(rows), seeds
MINE = {d: my_draw(LLAMA["members"], d) for d in range(1, 17)}
check(all(my_seed(DESIGN, STREAM, d, g) == derive_seed(DESIGN, STREAM, d, g) for d in (1, 16) for g in LLAMA["members"]),
      "my seed formula equals the engine's derive_seed")
check(len({tuple(MINE[d][0]) for d in MINE}) == 16, "16 distinct draws")
# off-by-one probe: no Llama file should equal a neighbouring draw
# ---- BLD by path ----
BLD = WS / ".ai/inputs/gate-b-sealed-20261008/build_sealed.py"
check(sha(BLD) == "80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6", "BLD pin (committed copy)")
check(sha(WS / "tmp/gate-b-sealed/build_sealed.py") == sha(BLD), "tmp BLD copy same bytes")
spec = importlib.util.spec_from_file_location("verifier_frozen_bld", BLD)
frozen = importlib.util.module_from_spec(spec); spec.loader.exec_module(frozen)
inputs = frozen.Inputs(WS / "tmp/kt-prepared/prepared-kt-dolly-olmo2")
for d in range(1, 17):
    remove, per_unit = frozen.draw_r(inputs, d)
    check(remove == MINE[d][0] and [u["seed"] for u in per_unit] == MINE[d][1], f"BLD draw_r(d={d}) equals my draw and seeds")
check(sha(BLD) == "80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6", "BLD unchanged after draw_r calls")
src_lines, _ = inspect.getsourcelines(derive_seed)
dsrc = shab("".join(src_lines).encode())
print(f"engine code_identity {code_identity()['sha256']}; derive_seed source sha {dsrc}")

# ---- the earlier files ----
SEAL = WS / ".ai/inputs/gate-b-sealed-20261008/out"
seal_man = json.loads((SEAL / "MANIFEST.json").read_bytes())
check(sha(SEAL / "MANIFEST.json") == "d76d8bf93bf39c246703f36a14fde3785c14b4e4728f15bf16e19fd972c279a8", "SEAL MANIFEST pin")
seal_listed = {f["path"]: f["sha256"] for f in seal_man["files"]}
RD = WS / ".ai/inputs/stage1-commitments-20261016/r-draws"
rec = json.loads((RD / "r_draws_record.json").read_bytes())
check(sha(RD / "r_draws_record.json") == "c09b20c135b483495987fd9dd2652ef3df31a7bc8fdbfe0581a1d3ce06882b6c", "stage-1 record pin")
rec_files = {f["file"]: f for f in rec["files"] if f["family"] == "R"}
check(sorted(rec_files) == sorted(f"edits/R_d{d}.json" for d in range(6, 11)), "stage-1 record lists R_d6-10")
for d in range(1, 6):
    doc = json.loads((SEAL / f"edits/R_d{d}.json").read_bytes())
    check(sha(SEAL / f"edits/R_d{d}.json") == seal_listed[f"edits/R_d{d}.json"], f"SEAL R_d{d} listed hash")
    check(doc["remove"] == MINE[d][0], f"SEAL R_d{d} remove == my draw")
    check([u["seed"] for u in doc["provenance"]["selection"]["per_unit"]] == MINE[d][1], f"SEAL R_d{d} per-unit seeds == mine")
for d in range(6, 11):
    doc = json.loads((RD / f"edits/R_d{d}.json").read_bytes())
    check(sha(RD / f"edits/R_d{d}.json") == rec_files[f"edits/R_d{d}.json"]["sha256"], f"stage-1 R_d{d} listed hash")
    check(doc["remove"] == MINE[d][0], f"stage-1 R_d{d} remove == my draw")
    check(rec_files[f"edits/R_d{d}.json"]["seed"] == 1100 + d and doc["provenance"]["stage1_wrapper"]["seed"] == 1100 + d, f"stage-1 R_d{d} seed 1100+d")
for u in sorted(LLAMA["members"]):
    doc = json.loads((SEAL / f"edits/unit_{u}.json").read_bytes())
    check(doc["remove"] == LLAMA["members"][u], f"SEAL unit_{u} == sorted Llama members")

# ---- the Llama set ----
LL = WS / ".ai/inputs/scale-78b-sealed-llama3-20261105"
WRAP_SHA = sha(LL / "build_sealed_llama3.py")
man = json.loads((LL / "out/MANIFEST.json").read_bytes())
print(f"Llama MANIFEST sha {sha(LL / 'out/MANIFEST.json')}; wrapper sha {WRAP_SHA}")
check(man["builder"]["sha256"] == WRAP_SHA, "MANIFEST builder sha == wrapper file")
check(man["engine"]["code_identity_sha256"] == code_identity()["sha256"], "MANIFEST engine identity == current")
check(man["engine"]["derive_seed"]["source_sha256"] == dsrc, "MANIFEST derive_seed source sha == current engine's")
check(man["prepared"]["written_for"]["manifest_sha256"] == LLAMA["manifest_sha"], "MANIFEST written_for == Llama")
check(man["prepared"]["written_for"]["read"]["engine/train_rows.jsonl"] == LLAMA["train_sha"], "MANIFEST Llama train_rows sha")
check(man["prepared"]["drawn_on"]["manifest_sha256"] == OLMO["manifest_sha"], "MANIFEST drawn_on == OLMo")
check(man["prepared"]["drawn_on"]["read"]["engine/train_rows.jsonl"] == OLMO["train_sha"], "MANIFEST OLMo train_rows sha")
on_disk = {p.relative_to(LL / "out").as_posix() for p in (LL / "out").rglob("*") if p.is_file()}
check(on_disk == {r["path"] for r in man["files"]} | {"MANIFEST.json"}, "out/ holds exactly the 24 listed files + MANIFEST")
for p in man["parity"]["sealed"]["files"]:
    check(man["parity"]["sealed"]["files"][p]["sha256"] == seal_listed[p] == sha(SEAL / p), f"parity.sealed {p} sha == SEAL")
for p in man["parity"]["stage1_r_draws"]["files"]:
    check(man["parity"]["stage1_r_draws"]["files"][p]["stage1_sha256"] == sha(RD / p), f"parity.stage1 {p} sha == stage 1")
llama_stub = type("Stub", (), {})(); llama_stub.manifest_sha256 = LLAMA["manifest_sha"]; llama_stub.train_rows = dict.fromkeys(LLAMA["tokens"]); llama_stub.groups = {"dev": dict(LLAMA["members"]), "heldout": {}}
olmo_stub = type("Stub", (), {})(); olmo_stub.manifest_sha256 = OLMO["manifest_sha"]; olmo_stub.train_rows = dict.fromkeys(OLMO["tokens"]); olmo_stub.groups = {"dev": dict(OLMO["members"]), "heldout": {}}
seeds_seen = set()
for r in man["files"]:
    p = LL / "out" / r["path"]; data = p.read_bytes(); doc = json.loads(data)
    check(shab(data) == r["sha256"] and r["arm"] == "edit-" + r["sha256"] and r["bytes"] == len(data), f"{r['path']}: MANIFEST sha/arm/bytes")
    check(canonical_json(doc) == data, f"{r['path']}: canonical bytes")
    check(doc["manifest_sha256"] == LLAMA["manifest_sha"], f"{r['path']}: manifest_sha256 == Llama")
    pv = doc["provenance"]
    check(pv["builder_sha256"] == WRAP_SHA and pv["frozen_builder"]["sha256"] == "80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6", f"{r['path']}: builder hashes")
    check(pv["inputs"]["manifest_sha256"] == LLAMA["manifest_sha"] and pv["inputs"]["engine/train_rows.jsonl"] == LLAMA["train_sha"] and pv["inputs"]["engine/groups.json"] == LLAMA["groups_sha"], f"{r['path']}: inputs hashes == Llama files")
    check(pv["drawn_on"]["manifest_sha256"] == OLMO["manifest_sha"] and pv["drawn_on"]["engine/train_rows.jsonl"] == OLMO["train_sha"], f"{r['path']}: drawn_on == OLMo files")
    check(pv["derive_seed"]["source_sha256"] == dsrc, f"{r['path']}: derive_seed source == current")
    check(doc["remove"] == sorted(set(doc["remove"])) and len(doc["remove"]) == 600 and doc["counts"] == {"remove": 600, "rewrite": 0, "add": 0}, f"{r['path']}: 600 sorted distinct")
    check(all(sum(1 for x in doc["remove"] if x in set(LLAMA["members"][g])) == (75 if r["family"] == "R" else (600 if g == r.get("unit") else 0)) for g in LLAMA["members"]), f"{r['path']}: per-unit counts")
    try:
        e = parse_edit(data, llama_stub); ok = e.removed == frozenset(doc["remove"]) and e.arm == arm_of(data)
    except EditError as exc:
        ok = False; print("   EditError on Llama stub:", type(exc).__name__)
    check(ok, f"{r['path']}: parse_edit accepts on Llama stub")
    try:
        parse_edit(data, olmo_stub); refused = False; msg = ""
    except EditError as exc:
        refused = True; msg = str(exc)
    check(refused and "manifest_sha256" in msg, f"{r['path']}: parse_edit refuses on OLMo stub (manifest)")
    if r["family"] == "R":
        d = r["draw"]
        check(doc["remove"] == MINE[d][0], f"{r['path']}: remove == my draw d={d}")
        check([u["seed"] for u in pv["selection"]["per_unit"]] == MINE[d][1], f"{r['path']}: per-unit seeds == mine")
        check(pv["selection"]["draw"] == d and pv["selection"]["stream"] == STREAM and pv["selection"]["design_seed"] == DESIGN, f"{r['path']}: selection draw/stream/design")
        check(pv["seed"] == 1100 + d == r["seed"] and pv["seed_map"]["offset"] == 1100, f"{r['path']}: seed 1100+d")
        seeds_seen.add(pv["seed"])
        for dd in (d - 1, d + 1):
            if 1 <= dd <= 16:
                check(doc["remove"] != MINE[dd][0], f"{r['path']}: not the neighbouring draw d={dd}")
        same = pv["same_rows_as"]
        if d <= 5:
            check(same["file"] == f".ai/inputs/gate-b-sealed-20261008/out/edits/R_d{d}.json" and same["sha256"] == sha(SEAL / f"edits/R_d{d}.json"), f"{r['path']}: same_rows_as SEAL (path, sha)")
        elif d <= 10:
            check(same["file"] == f".ai/inputs/stage1-commitments-20261016/r-draws/edits/R_d{d}.json" and same["sha256"] == sha(RD / f"edits/R_d{d}.json"), f"{r['path']}: same_rows_as stage 1 (path, sha)")
        else:
            check(same["file"] is None, f"{r['path']}: same_rows_as None")
    else:
        u = r["unit"]
        check(doc["remove"] == LLAMA["members"][u] and pv["selection"]["unit"] == u and pv["selection"]["category"] == LLAMA["cats"][u] == r["category"], f"{r['path']}: unit members/category")
        check(pv["same_rows_as"]["sha256"] == sha(SEAL / f"edits/unit_{u}.json"), f"{r['path']}: same_rows_as SEAL unit sha")
check(seeds_seen == set(range(1101, 1117)), "R seeds 1101-1116")
check({r["unit"] for r in man["files"] if r["family"] == "unit"} == set(LLAMA["members"]), "8 unit files cover the 8 groups")

# ---- the OLMo d = 11-16 folder ----
RO = WS / ".ai/inputs/scale-78b-r-draws-olmo2-20261105"
rman = json.loads((RO / "out/MANIFEST.json").read_bytes())
RSCRIPT_SHA = sha(WS / "scripts/scale78b/build_r_draws_78b.py")
print(f"r-draws MANIFEST sha {sha(RO / 'out/MANIFEST.json')}; script sha {RSCRIPT_SHA}")
check(rman["script"]["sha256"] == RSCRIPT_SHA, "r-draws MANIFEST script sha == file")
check([r["path"] for r in rman["files"]] == [f"edits/R_d{d}.json" for d in range(11, 17)], "r-draws lists R_d11-16")
base_seal = dict(json.loads((SEAL / "edits/R_d1.json").read_bytes())["provenance"]); base_seal.pop("selection")
for r in rman["files"]:
    d = r["draw"]; p = RO / "out" / r["path"]; data = p.read_bytes(); doc = json.loads(data)
    check(shab(data) == r["sha256"] and r["arm"] == "edit-" + r["sha256"], f"OLMo R_d{d}: MANIFEST sha/arm")
    check(canonical_json(doc) == data, f"OLMo R_d{d}: canonical bytes")
    check(doc["manifest_sha256"] == OLMO["manifest_sha"], f"OLMo R_d{d}: manifest == OLMo")
    check(doc["remove"] == MINE[d][0] and [u["seed"] for u in doc["provenance"]["selection"]["per_unit"]] == MINE[d][1], f"OLMo R_d{d}: remove and seeds == mine")
    check(doc["provenance"]["selection"]["draw"] == d and doc["provenance"]["scale78b_wrapper"]["seed"] == 1100 + d == r["seed"], f"OLMo R_d{d}: draw d, seed 1100+d")
    check(doc["provenance"]["scale78b_wrapper"]["script_sha256"] == RSCRIPT_SHA, f"OLMo R_d{d}: wrapper script sha")
    pv_wo = {k: v for k, v in doc["provenance"].items() if k not in ("selection", "scale78b_wrapper")}
    check(pv_wo == base_seal, f"OLMo R_d{d}: provenance outside selection/scale78b_wrapper == SEAL R_d1's base")
    check(doc["name"] == f"gate-b R_{d}: remove 75 rows of each of the 8 units at random (600 rows)", f"OLMo R_d{d}: BLD's name form")
    try:
        parse_edit(data, olmo_stub); ok = True
    except EditError:
        ok = False
    check(ok, f"OLMo R_d{d}: parse_edit accepts on OLMo stub")
    try:
        parse_edit(data, llama_stub); refused = False
    except EditError as exc:
        refused = "manifest_sha256" in str(exc)
    check(refused, f"OLMo R_d{d}: parse_edit refuses on Llama stub")
    # BLD's own edit_file reproduces these bytes?
    sel = doc["provenance"]["selection"]
    data2, _ = frozen.edit_file(inputs, doc["name"], MINE[d][0], {**base_seal, "selection": sel, "scale78b_wrapper": doc["provenance"]["scale78b_wrapper"]}, frozen.EnginePrepared(inputs))
    check(data2 == data, f"OLMo R_d{d}: BLD edit_file with the recorded blocks gives the same bytes")
on_disk_r = {p.relative_to(RO / "out").as_posix() for p in (RO / "out").rglob("*") if p.is_file()}
check(on_disk_r == {f"edits/R_d{d}.json" for d in range(11, 17)} | {"MANIFEST.json"}, "r-draws out/ holds exactly 6 + MANIFEST")

print(f"\nFAILS: {len(FAILS)}")
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
