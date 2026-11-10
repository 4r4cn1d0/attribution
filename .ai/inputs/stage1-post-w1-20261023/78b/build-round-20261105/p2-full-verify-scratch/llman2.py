import json, subprocess
MAIN="/Users/spiderishi/Coding/attribution"
d=json.loads(subprocess.run(["git","-C",MAIN,"show","HEAD:.ai/inputs/scale-78b-sealed-llama3-20261105/out/MANIFEST.json"],capture_output=True,check=True).stdout)
for k in ("sealed","stage1_r_draws"):
    fs=d["parity"][k]["files"]
    print(k, type(fs).__name__, len(fs))
    for name,v in (fs.items() if isinstance(fs,dict) else enumerate(fs)):
        print("  ", name, {a:b for a,b in v.items() if isinstance(b,bool)} if isinstance(v,dict) else type(v).__name__)
