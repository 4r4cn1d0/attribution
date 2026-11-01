import datetime as dt, hashlib, json, pathlib, sys
ledger, step, code, *rest = sys.argv[1:]
notes = [x[5:] for x in rest if x.startswith("note=")]
files = [x for x in rest if not x.startswith("note=")]
rec = {"utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"), "step": step, "exit": int(code),
       "outputs": {f: hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest() for f in files if pathlib.Path(f).is_file()}}
if notes:
    rec["note"] = notes[0]
with open(ledger, "a" if pathlib.Path(ledger).exists() else "x") as handle:   # created once (R0-start), then appended
    handle.write(json.dumps(rec, sort_keys=True) + "\n")
print(json.dumps(rec, sort_keys=True))
