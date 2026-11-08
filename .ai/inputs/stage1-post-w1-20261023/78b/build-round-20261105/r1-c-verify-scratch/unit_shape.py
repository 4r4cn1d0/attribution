"""Verifier scratch: does each real side a0 unit's COMPLETE.json have the shape tau_l_78b.read_unit expects?
Prints booleans and the SHA-256 match only: no value, no loss, no count. Opens COMPLETE.json only (never
query_loss.jsonl or any other file; the loss file is checked by stat and by name in COMPLETE.json's file list)."""
import hashlib, json, math, sys
from pathlib import Path
MAIN = Path(sys.argv[1])
UNITS = {
 ("olmo2-7b", 1101): "tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-e1-a1",
 ("olmo2-7b", 1102): "tmp/family-probe-sp-olmo2-7b-b-seed1102/retrieved/sp-olmo2-7b-1102/tree/round1/1102-a0-e1-a1",
 ("olmo2-7b", 1103): "tmp/family-probe-sp-olmo2-7b-b-seed1103/retrieved/sp-olmo2-7b-1103/tree/round1/1103-a0-e1-a1",
 ("llama31-8b", 1101): "tmp/family-probe-sp-llama31-8b-b5e5-1101/retrieved/sp-llama31-8b-b5e5-1101/tree/round1/1101-a0-e1-a1",
 ("llama31-8b", 1102): "tmp/family-probe-sp-llama31-8b-b5e5-seed1102/retrieved/sp-llama31-8b-b5e5-1102/tree/round1/1102-a0-e1-a1"}
PINS = {("olmo2-7b", 1101): "4a6d9ebc6636de57d52ec1b9cc1cd82afb1bdbfbf2a70e3f9884d3e9404d6dfc",
        ("olmo2-7b", 1102): "43e8412dc7ef8d3eb017340a788e08041623bce8b3896a750d6cc50e10e282c4",
        ("olmo2-7b", 1103): "4b5bd06dede08dc14f3ab5de201b7618ada94a0515896ed23c04b3af7ca44fa0",
        ("llama31-8b", 1101): "21427715565fb394220a068c8991b8f6819c4773ccf82b0cd7c35fe3788bc22a",
        ("llama31-8b", 1102): "b0c99f7b97e6e76355383644ee50f9cbef33c25e09585a9a0d030712d4aa75d9"}
TI = {"olmo2-7b": "36738c3823fae7eaca625cc9f619e98c7e40b9bb64e5d0e234412827d3371ec6",
      "llama31-8b": "5b4451e1487fb2200a5b2b151de2e68397117099a429654484146b3cc3791287"}
MAN = {"olmo2-7b": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9",
       "llama31-8b": "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"}
LOSS = "eval/e1/query_loss.jsonl"
banks = {}
for (fam, seed), rel in UNITS.items():
    folder = MAIN / rel
    data = (folder / "COMPLETE.json").read_bytes()
    m = json.loads(data)
    ev = m.get("evaluation") or {}
    ql = ev.get("query_loss") or {}
    ident = m.get("identity") or {}
    traj = m.get("trajectory") or {}
    mean = ql.get("mean")
    checks = {
        "pin": hashlib.sha256(data).hexdigest() == PINS[(fam, seed)],
        "complete": m.get("complete") is True, "files_dict": isinstance(m.get("files"), dict),
        "target_e1": m.get("target_checkpoint") == "e1", "arm_a0": traj.get("arm") == "a0", "seed": traj.get("seed") == seed,
        "training_identity": ident.get("training_identity") == TI[fam], "manifest": ident.get("manifest_sha256") == MAN[fam],
        "eval_e1": ev.get("checkpoint") == "e1", "n200": ql.get("n") == 200,
        "mean_finite_float": isinstance(mean, float) and math.isfinite(mean),
        "bank_hex64": isinstance(ql.get("query_bank_sha256"), str) and len(ql["query_bank_sha256"]) == 64,
        "loss_listed": isinstance((m.get("files") or {}).get(LOSS), str), "loss_file_exists": (folder / LOSS).is_file(),
        "no_error_txt": not (folder / "error.txt").exists()}
    banks.setdefault(fam, set()).add(ql.get("query_bank_sha256"))
    print(fam, seed, "all" if all(checks.values()) else "FAIL", {k: v for k, v in checks.items() if not v})
for fam, b in banks.items():
    print(fam, "one query bank across its side units:", len(b) == 1)
