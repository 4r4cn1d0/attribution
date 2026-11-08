"""Smoke: real_context on both families' prepared sets (manifest + offline tokenizer only) and the count functions on
SYNTHETIC text. Prints counts and hashes only."""
import sys
from pathlib import Path
WS = Path(sys.argv[1]); sys.path.insert(0, str(WS))
from scripts.scale78b import encode_count_78b as ec
MAIN = Path("/Users/spiderishi/Coding/attribution")
for fam, name in (("olmo2-7b", "prepared-kt-dolly-olmo2"), ("llama31-8b", "prepared-kt-dolly-llama3")):
    ctx = ec.real_context(fam, MAIN / "tmp/kt-prepared" / name)
    recipe, sha, label, limits = ec.load_recipe(fam, None)
    tk = ec.check_tokenizer(recipe, ctx)
    rows = [("a", "Write a short poem about rivers."), ("b", "word " * 1600), ("c", "")]
    gen = ec.refusals_generation(ctx.codec, rows, limits["max_prompt_tokens"])
    tr = ec.refusals_train(ctx.codec, [("a", "Say hi.", "Hi there."), ("b", "Say hi.", ""), ("c", "x", "word " * 3100)],
                           limits["max_train_tokens"])
    print(fam, ctx.manifest_sha256[:16], tk, limits, "gen refusals", gen, "train refusals", tr)
