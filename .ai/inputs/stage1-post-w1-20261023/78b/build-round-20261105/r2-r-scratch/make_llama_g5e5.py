"""Writes Llama-3.1-8B's recipe-G config at LR 5e-5 (DES F2; GXB O11): the LR 1e-4 G config with train.lr, name and
purpose changed, key order and the 4-space form kept. Run once by the R2 Track R builder; kept as evidence."""
import json, sys
from pathlib import Path
WS = Path(sys.argv[1])
src = WS / "experiments/safety_selection/configs/study-kt-llama31-8b-r64-g-mb2-20261011.json"
name = "study-kt-llama31-8b-r64-g5e5-mb2-20261108"
out = WS / f"experiments/safety_selection/configs/{name}.json"
d = json.loads(src.read_bytes())
assert d["train"]["lr"] == 0.0001
d["name"] = name
d["purpose"] = ("Recipe G at LR 5e-5 for Llama-3.1-8B, the 7-8B tier's recipe-G reference (Part 2 section 3.2; the "
                "lead's design ruling DES F2 of 6 Nov 2026: on Llama a new G config at LR 5e-5; build ruling GXB O11 of "
                "8 Nov 2026; R2 Track R, 8 Nov 2026): study-kt-llama31-8b-r64-g-mb2-20261011 with train.lr 5e-5 (was "
                "1e-4), the main recipe's LR on this family (study-kt-llama31-8b-r64-b5e5-mb2-20261010), and nothing "
                "else changed: recipe G is the 1B B -> G train change (token-mean loss and loss_weighting, "
                "warmup_cosine schedule, 4 warmup steps, schedule_until e1) at the family's main LR. The generation and "
                "guard blocks are the main recipe's, so one O-ext cap and one judge serve the family.")
d["train"]["lr"] = 5e-05
assert not out.exists()
out.write_bytes((json.dumps(d, indent=4, ensure_ascii=False) + "\n").encode("utf-8"))
print(out)
