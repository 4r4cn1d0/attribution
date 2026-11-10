"""Independent integrity check of ws-c's three sealed sets: hashes, arms, embedded script hashes, seal fields,
membership (ids only), list equality against SEAL / stage 1 / OLMo d11-16. Prints counts and hashes only."""
import hashlib, json, pathlib, sys
WS = pathlib.Path(sys.argv[1])
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def J(p): return json.loads(pathlib.Path(p).read_bytes())
ok = fails = 0
def check(cond, label):
    global ok, fails
    if cond: ok += 1
    else:
        fails += 1; print("FAIL", label)
LS = WS / ".ai/inputs/scale-78b-sealed-llama3-20261105"
RD = WS / ".ai/inputs/scale-78b-r-draws-olmo2-20261105"
H1 = WS / ".ai/inputs/scale-78b-length-rules-llama3-20261105"
SEAL = WS / ".ai/inputs/gate-b-sealed-20261008/out"
ST1 = WS / ".ai/inputs/stage1-commitments-20261016/r-draws"
LLAMA_M = "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"
OLMO_M = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
w_sealed = sha(LS / "build_sealed_llama3.py"); w_rd = sha(WS / "scripts/scale78b/build_r_draws_78b.py"); w_h1 = sha(WS / "scripts/scale78b/build_h1_llama3.py")
print("wrapper hashes", w_sealed[:8], w_rd[:8], w_h1[:8])
groups = {g["group_id"]: set(g["members"]) for g in J(WS / "tmp/kt-prepared/prepared-kt-dolly-llama3/engine/groups.json")["partitions"]["dev"]["groups"]}
ogroups = {g["group_id"]: set(g["members"]) for g in J(WS / "tmp/kt-prepared/prepared-kt-dolly-olmo2/engine/groups.json")["partitions"]["dev"]["groups"]}
check(groups == ogroups, "dev groups equal across the two prepared sets")
check(sha(WS / "tmp/kt-prepared/prepared-kt-dolly-llama3/manifest.json") == LLAMA_M, "llama manifest pin")
check(sha(WS / "tmp/kt-prepared/prepared-kt-dolly-olmo2/manifest.json") == OLMO_M, "olmo manifest pin")
# --- Llama sealed set
man = J(LS / "out/MANIFEST.json"); listed = {f["path"]: f for f in man["files"]}
check(len(listed) == 24, "24 files listed"); check(man["builder"]["sha256"] == w_sealed, "MANIFEST builder sha == wrapper bytes")
ondisk = sorted(p.relative_to(LS / "out").as_posix() for p in (LS / "out").rglob("*") if p.is_file())
check(set(ondisk) == set(listed) | {"MANIFEST.json"}, "on-disk files == listed + MANIFEST")
seal_listed = {f["path"]: f["sha256"] for f in J(SEAL / "MANIFEST.json")["files"]}
st1_rec = {f["file"]: f for f in J(ST1 / "r_draws_record.json")["files"]}
for rel, rec in listed.items():
    p = LS / "out" / rel; data = p.read_bytes(); h = hashlib.sha256(data).hexdigest(); doc = json.loads(data)
    check(h == rec["sha256"], f"{rel} sha"); check(rec["arm"] == "edit-" + h, f"{rel} arm")
    check(doc["kind"] == "safety-selection edit" and doc["edit_kind"] == "remove", f"{rel} kind/edit_kind")
    check(doc["manifest_sha256"] == LLAMA_M, f"{rel} manifest"); check(doc["rewrite"] == [] and doc["add"] == [], f"{rel} rewrite/add empty")
    check(doc["counts"] == {"remove": len(doc["remove"]), "rewrite": 0, "add": 0}, f"{rel} counts")
    rows = doc["remove"]; check(rows == sorted(set(rows)) and len(rows) == 600, f"{rel} 600 sorted distinct")
    check(doc["provenance"]["builder_sha256"] == w_sealed, f"{rel} embedded builder sha")
    check(doc["provenance"]["frozen_builder"]["sha256"] == "80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6", f"{rel} BLD pin")
    check(doc["provenance"]["inputs"]["manifest_sha256"] == LLAMA_M, f"{rel} prov inputs manifest")
    if rel.startswith("edits/R_d"):
        d = int(rel[len("edits/R_d"):-5]); sel = doc["provenance"]["selection"]
        check(sel["family"] == "R" and sel["draw"] == d, f"{rel} selection family/draw"); check(doc["provenance"]["seed"] == 1100 + d, f"{rel} seed")
        check(rec.get("seed") == 1100 + d and rec.get("draw") == d and rec.get("family") == "R", f"{rel} manifest record seed/draw")
        check(all(sum(1 for r in rows if r in groups[u]) == 75 for u in groups), f"{rel} 75 per unit")
        if d <= 5:
            s = J(SEAL / rel); check(rows == s["remove"], f"{rel} == SEAL remove"); check(doc["provenance"]["same_rows_as"]["sha256"] == seal_listed[rel] == sha(SEAL / rel), f"{rel} same_rows_as SEAL hash")
        elif d <= 10:
            s = J(ST1 / rel); check(rows == s["remove"], f"{rel} == stage1 remove"); check(doc["provenance"]["same_rows_as"]["sha256"] == st1_rec[rel]["sha256"] == sha(ST1 / rel), f"{rel} same_rows_as stage1 hash")
            check(st1_rec[rel]["seed"] == 1100 + d, f"{rel} stage1 seed")
        else:
            o = J(RD / "out" / rel); check(rows == o["remove"], f"{rel} == OLMo d11-16 remove"); check(doc["provenance"]["same_rows_as"]["file"] is None, f"{rel} same_rows_as None")
    else:
        u = rel[len("edits/unit_"):-5]; check(set(rows) == groups[u], f"{rel} == group members")
        check(set(rows) == set(J(SEAL / rel)["remove"]), f"{rel} == SEAL unit")
lists = [tuple(J(LS / f"out/edits/R_d{d}.json")["remove"]) for d in range(1, 17)]; check(len(set(lists)) == 16, "16 distinct Llama draws")
# --- OLMo d11-16
man = J(RD / "out/MANIFEST.json"); check(man["script"]["sha256"] == w_rd, "r-draws MANIFEST script sha == bytes")
check([f["path"] for f in man["files"]] == [f"edits/R_d{d}.json" for d in range(11, 17)], "r-draws 6 files")
for rec in man["files"]:
    p = RD / "out" / rec["path"]; data = p.read_bytes(); h = hashlib.sha256(data).hexdigest(); doc = json.loads(data); d = rec["draw"]
    check(h == rec["sha256"] and rec["arm"] == "edit-" + h and rec["seed"] == 1100 + d, f"rd {rec['path']} sha/arm/seed")
    check(doc["kind"] == "safety-selection edit" and doc["edit_kind"] == "remove" and doc["manifest_sha256"] == OLMO_M, f"rd {rec['path']} seal fields")
    sel = doc["provenance"]["selection"]; check(sel["family"] == "R" and sel["draw"] == d, f"rd {rec['path']} selection")
    check(doc["provenance"]["scale78b_wrapper"]["script_sha256"] == w_rd and doc["provenance"]["scale78b_wrapper"]["seed"] == 1100 + d, f"rd {rec['path']} wrapper sha/seed")
    check(doc["provenance"]["builder_sha256"] == "80cb8944cbea2847a4d39cddae225158f98431a8612282e2dd7161239050d3c6", f"rd {rec['path']} BLD")
    rows = doc["remove"]; check(rows == sorted(set(rows)) and len(rows) == 600 and all(sum(1 for r in rows if r in ogroups[u]) == 75 for u in ogroups), f"rd {rec['path']} 600/75")
    check("seed" not in doc["provenance"] or doc["provenance"].get("seed") in (None, 1100 + d), f"rd {rec['path']} top-level seed")
rep = man["reproduction"]; check(all(rep["sealed"]["files"][f"edits/R_d{d}.json"]["byte_identical"] for d in range(1, 6)), "rd reproduction sealed flags")
check(all(rep["stage1_r_draws"]["files"][f"edits/R_d{d}.json"]["remove_list_equal"] for d in range(6, 11)), "rd reproduction stage1 flags")
# --- H1
man = J(H1 / "out/MANIFEST.json"); check(man["script"]["sha256"] == w_h1, "H1 MANIFEST script sha == bytes")
p = H1 / "out/edits/octile_0.json"; data = p.read_bytes(); h = hashlib.sha256(data).hexdigest(); doc = json.loads(data); rec = man["files"][0]
check(h == rec["sha256"] and rec["arm"] == "edit-" + h and rec["path"] == "edits/octile_0.json" and len(man["files"]) == 1, "H1 sha/arm")
check(doc["provenance"]["script_sha256"] == w_h1, "H1 embedded script sha"); check(doc["manifest_sha256"] == LLAMA_M and doc["edit_kind"] == "remove", "H1 manifest/kind")
check(len(doc["remove"]) == 600 == len(set(doc["remove"])) and doc["remove"] == sorted(doc["remove"]), "H1 600 sorted")
check(man["stage1_h1_on_olmo"]["sha256"] == sha(WS / ".ai/inputs/stage1-commitments-20261016/length-rules/edits/octile_0.json"), "H1 stage-1 pin equals the file")
# --- the G1 record's embedded hashes
g1 = J(WS / ".ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105.json")
check(g1["noise_reading_sha256"] == sha(WS / "scripts/scale78b/noise_reading.py"), "G1 record noise_reading_sha256 == bytes")
check(g1["script_sha256"] == sha(WS / "scripts/scale78b/g1_check_78b.py"), "G1 record script_sha256 == bytes")
check(g1["inputs_sha256"] == sha(WS / ".ai/inputs/stage1-post-w1-20261023/78b/llama-g1-check-20261105-units.json"), "G1 record inputs_sha256 == units file")
print("by_family:", json.dumps(g1.get("by_family"))[:300])
print(f"OK {ok}  FAILS {fails}")
