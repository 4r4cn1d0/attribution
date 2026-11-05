"""Verifier's independent recomputation of H1 (track B, 3rd priority). Counts, hashes, token values and booleans only;
no row id and no text is printed. Reads the registry entry length.order from scripts/stage1/labels.json itself and
re-derives the sealed rank with its own sha256 seed and random.Random(seed).shuffle(sorted(ids))."""
import hashlib, json, random, sys
from pathlib import Path

WS = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(WS))
from experiments.safety_selection.common import code_identity  # noqa: E402
from experiments.safety_selection.edits import EditError, parse_edit  # noqa: E402

FAILS = []
def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def read_set(root: Path):
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    tokens = {}
    with open(root / "engine/train_rows.jsonl", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line); rid, tt = row["row_id"], row["target_tokens"]; row.clear(); del row
            tokens[rid] = tt
    groups = json.loads((root / "engine/groups.json").read_bytes())["partitions"]
    members = {g["group_id"]: sorted(g["members"]) for g in groups["dev"]["groups"]}
    cats = {gid: u["category"] for gid, u in manifest["units"].items()}
    return {"manifest_sha": hashlib.sha256(manifest_bytes).hexdigest(), "tokens": tokens, "members": members, "cats": cats,
            "train_sha": sha(root / "engine/train_rows.jsonl")}

OLMO = read_set(WS / "tmp/kt-prepared/prepared-kt-dolly-olmo2")
LLAMA = read_set(WS / "tmp/kt-prepared/prepared-kt-dolly-llama3")

reg = json.loads((WS / "scripts/stage1/labels.json").read_bytes())
entry = reg["labels"]["length.order"]
print("length.order entry:", json.dumps(entry))
check(entry["parts"] == [] and entry["base_seed"] == 20261008, "length.order takes no parts, base seed 20261008")
def my_seed(*parts):
    return int.from_bytes(hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()[:8], "big")
def my_h1(tokens):
    ids = sorted(tokens)
    random.Random(my_seed(20261008, entry["label"])).shuffle(ids)
    rank = {r: i for i, r in enumerate(ids)}
    order = sorted(tokens, key=lambda r: (tokens[r], rank[r]))
    parts = [order[600 * k: 600 * (k + 1)] for k in range(8)]
    cuts = [(tokens[p[0]], tokens[p[-1]]) for p in parts]
    return sorted(parts[0]), cuts, rank, order

H1_L, CUTS_L, RANK, ORDER_L = my_h1(LLAMA["tokens"])
H1_O, CUTS_O, _, ORDER_O = my_h1(OLMO["tokens"])
print("my Llama cut points:", CUTS_L)
print("my OLMo  cut points:", CUTS_O)

# stage 1's committed H1 on OLMo
S1 = WS / ".ai/inputs/stage1-commitments-20261016/length-rules/edits/octile_0.json"
s1doc = json.loads(S1.read_bytes())
check(sha(S1) == "f5b1762f662e931235f798497248b2f342e6d2b2011ce5a0bfecf53678b4def7", "stage-1 octile_0 pin")
check(s1doc["remove"] == H1_O, "my OLMo H1 == stage 1's committed octile_0 remove list")
check(s1doc["manifest_sha256"] == OLMO["manifest_sha"], "stage-1 octile_0 on the OLMo manifest")

# the builder's Llama H1
HL = WS / ".ai/inputs/scale-78b-length-rules-llama3-20261105"
doc = json.loads((HL / "out/edits/octile_0.json").read_bytes())
man = json.loads((HL / "out/MANIFEST.json").read_bytes())
print(f"Llama H1 sha {sha(HL / 'out/edits/octile_0.json')}; MANIFEST sha {sha(HL / 'out/MANIFEST.json')}")
check(doc["remove"] == H1_L, "builder's Llama H1 remove list == my recomputation")
check(doc["manifest_sha256"] == LLAMA["manifest_sha"], "Llama H1 on the Llama manifest")
check(len(doc["remove"]) == 600 and doc["remove"] == sorted(set(doc["remove"])), "600 sorted distinct")
check(doc["counts"] == {"remove": 600, "rewrite": 0, "add": 0} and doc["rewrite"] == [] and doc["add"] == [], "remove-only edit")
check(set(doc) == {"kind", "version", "name", "edit_kind", "manifest_sha256", "remove", "rewrite", "add", "position_rule", "counts", "provenance"}, "exactly the engine's keys")
pv = doc["provenance"]
check(not any(k in ("prompt", "response", "text") for k in pv), "no text keys in provenance")
longest = max(len(v) for v in json.dumps(pv).split('"') )
print("longest quoted string in provenance (chars):", longest)
check(pv["script_sha256"] == sha(WS / "scripts/scale78b/build_h1_llama3.py"), "H1 provenance script sha == file")
check(pv["rule_from"]["sha256"] == sha(WS / "scripts/stage1/build_length_rules.py"), "rule_from sha == committed build_length_rules.py")
check(pv["s1common_sha256"] == sha(WS / "scripts/stage1/s1common.py"), "s1common sha == committed")
check(pv["settings"]["sha256"] == sha(WS / "scripts/stage1/settings/build_length_rules.json"), "settings sha == committed")
check(pv["inputs"]["prepared_manifest"] == LLAMA["manifest_sha"] and pv["inputs"]["prepared_train_rows"] == LLAMA["train_sha"], "inputs == Llama manifest/train_rows")
check(pv["engine_identity_sha256"] == code_identity()["sha256"], "engine identity == current")
check([(c["first_target_tokens"], c["last_target_tokens"]) for c in pv["cut_points"]] == CUTS_L, "cut points == mine (Llama)")
check([(c["first_target_tokens"], c["last_target_tokens"]) for c in man["cut_points"]] == CUTS_L, "MANIFEST cut points == mine")
by_cat = {}
for g, rows in LLAMA["members"].items():
    by_cat[LLAMA["cats"][g]] = sum(1 for r in rows if r in set(H1_L))
check(pv["by_category"] == by_cat == man["files"][0]["by_category"], "by_category == mine")
rec = man["files"][0]
check(rec["sha256"] == sha(HL / "out/edits/octile_0.json") and rec["arm"] == "edit-" + rec["sha256"] and rec["rows"] == 600, "MANIFEST record sha/arm/rows")
check(man["script"]["sha256"] == pv["script_sha256"], "MANIFEST script sha")
check(man["stage1_h1_on_olmo"]["sha256"] == sha(S1), "MANIFEST names stage 1's H1 by its real hash")
# token accounting re-check (target tokens; total needs prompt_tokens, read separately below)
removed_target = sum(LLAMA["tokens"][r] for r in H1_L)
total_target = sum(LLAMA["tokens"].values())
check(rec["tokens"]["removed"]["target_tokens"] == removed_target and rec["tokens"]["corpus"]["target_tokens"] == total_target, "target-token accounting")
check(rec["tokens"]["edited_corpus"]["rows"] == 4200 and rec["tokens"]["edited_corpus"]["steps"] == -(-4200 // 128), "edited corpus rows 4200, steps ceil(4200/128)")
on_disk = {p.relative_to(HL / "out").as_posix() for p in (HL / "out").rglob("*") if p.is_file()}
check(on_disk == {"edits/octile_0.json", "MANIFEST.json"}, "H1 out/ holds exactly 2 files")
# parse_edit
llama_stub = type("S", (), {})(); llama_stub.manifest_sha256 = LLAMA["manifest_sha"]; llama_stub.train_rows = dict.fromkeys(LLAMA["tokens"]); llama_stub.groups = {"dev": dict(LLAMA["members"]), "heldout": {}}
olmo_stub = type("S", (), {})(); olmo_stub.manifest_sha256 = OLMO["manifest_sha"]; olmo_stub.train_rows = dict.fromkeys(OLMO["tokens"]); olmo_stub.groups = {"dev": dict(OLMO["members"]), "heldout": {}}
data = (HL / "out/edits/octile_0.json").read_bytes()
try:
    e = parse_edit(data, llama_stub); ok = e.removed == frozenset(H1_L)
except EditError:
    ok = False
check(ok, "parse_edit accepts Llama H1 on the Llama stub")
try:
    parse_edit(data, olmo_stub); refused = False
except EditError as exc:
    refused = "manifest_sha256" in str(exc)
check(refused, "parse_edit refuses Llama H1 on the OLMo stub")

# the difference between the two H1s (mechanism; counts and token values only)
sym = set(H1_L) ^ set(H1_O)
enter = set(H1_L) - set(H1_O); leave = set(H1_O) - set(H1_L)
print(f"Llama H1 vs OLMo H1: shared {len(set(H1_L) & set(H1_O))}, enter {len(enter)}, leave {len(leave)}")
for r in enter:
    print(f"  entering row: olmo tokens {OLMO['tokens'][r]} -> llama tokens {LLAMA['tokens'][r]}, rank {RANK[r]}")
for r in leave:
    print(f"  leaving row: olmo tokens {OLMO['tokens'][r]} -> llama tokens {LLAMA['tokens'][r]}, rank {RANK[r]}")
inside_diff = sum(1 for r in H1_O if OLMO["tokens"][r] != LLAMA["tokens"][r])
inside_diff_l = sum(1 for r in H1_L if OLMO["tokens"][r] != LLAMA["tokens"][r])
print(f"rows with changed counts inside OLMo H1: {inside_diff}; inside Llama H1: {inside_diff_l}")
check(len(sym) == 2 and len(enter) == 1 and len(leave) == 1, "exactly one row enters and one leaves (builder's claim)")
# the worst-ranked 13-token row claim
at13 = [r for r in H1_O if OLMO["tokens"][r] == 13]
if leave:
    lv = next(iter(leave))
    check(RANK[lv] == max(RANK[r] for r in at13), "the leaving row is the worst-ranked 13-token row of the OLMo H1")
    check(OLMO["tokens"][lv] == LLAMA["tokens"][lv] == 13, "the leaving row's count is 13 in both sets")
if enter:
    en = next(iter(enter))
    check(OLMO["tokens"][en] == 14 and LLAMA["tokens"][en] == 13, "the entering row's count falls 14 -> 13")
print(f"\nFAILS: {len(FAILS)}")
for f in FAILS: print("  -", f)
sys.exit(1 if FAILS else 0)
