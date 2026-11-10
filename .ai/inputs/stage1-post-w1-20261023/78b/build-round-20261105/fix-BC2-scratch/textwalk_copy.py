"""Walk every new JSON output in ws-c for text: the longest string, strings with newlines, suspicious keys. Prints lengths, key names and counts only, never a string's content."""
import json, pathlib, re, sys
WS = pathlib.Path(sys.argv[1])
files = sorted(list((WS / ".ai/inputs/scale-78b-sealed-llama3-20261105/out").rglob("*.json")) + list((WS / ".ai/inputs/scale-78b-r-draws-olmo2-20261105/out").rglob("*.json")) + list((WS / ".ai/inputs/scale-78b-length-rules-llama3-20261105/out").rglob("*.json")) + list((WS / ".ai/inputs/stage1-post-w1-20261023/78b").glob("llama-g1-check-*.json")))
SUSP = re.compile(r"prompt|response|answer|completion|instruction|text|output|generation|sample|message|content", re.I)
ROWID = re.compile(r"^[a-z0-9-]{1,40}$")
total = 0
for f in files:
    doc = json.loads(f.read_bytes()); longest = (0, ""); newlines = 0; susp_keys = set(); nstr = 0; nonid_long = 0
    def walk(o, path=""):
        global longest, newlines, nstr, nonid_long
        if isinstance(o, dict):
            for k, v in o.items():
                if SUSP.search(str(k)) and not str(k).endswith("_tokens") and k not in ("fields_read",): susp_keys.add(f"{path}/{k}")
                walk(v, f"{path}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o): walk(v, f"{path}[{i}]" if not path.endswith("]") else path)
        elif isinstance(o, str):
            nstr += 1
            if "\n" in o: newlines += 1
            if len(o) > longest[0]: longest = (len(o), path)
            if len(o) > 80 and not ROWID.match(o): nonid_long += 1
    walk(doc); total += 1
    print(f"{f.relative_to(WS)}: strings {nstr}, longest {longest[0]} at {longest[1]}, newlines {newlines}, >80 non-id {nonid_long}, suspicious keys {sorted(susp_keys)[:6]}")
print("files walked", total)
